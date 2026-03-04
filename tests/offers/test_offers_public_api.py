from typing import Any, Callable, Generator
from unittest.mock import Mock, create_autospec

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.core.config import settings
from app.core.current_user import get_current_user
from app.core.database import get_db
from app.core.errors.codes import ErrorCode
from app.main import app
from app.offers.composition import get_offer_service
from app.offers.models import Offer
from app.offers.services import OfferService


@pytest.fixture
def offer_service_mock() -> Mock:
    return create_autospec(OfferService)


@pytest.fixture
def user_client(offer_service_mock: Mock) -> Generator[TestClient, None, None]:
    """TestClient for user-authenticated endpoints (uses get_current_user, not admin)."""

    def mock_get_db() -> Generator[Mock, None, None]:
        yield Mock()

    app.dependency_overrides[get_db] = mock_get_db
    app.dependency_overrides[get_offer_service] = lambda: offer_service_mock
    app.dependency_overrides[get_current_user] = lambda: Mock()

    yield TestClient(app)

    app.dependency_overrides.clear()


def _assert_error_code(data: dict[str, Any], expected_code: str) -> None:
    assert "error" in data
    assert data["error"]["code"] == expected_code


def _assert_active_offers_response(
    data: dict[str, Any],
    items: list[tuple[Offer, str]],
    total: int,
    page: int,
    page_size: int,
) -> None:
    assert data["total"] == total
    assert data["page"] == page
    assert data["page_size"] == page_size
    assert len(data["offers"]) == len(items)
    for i, (offer, merchant_name) in enumerate(items):
        item = data["offers"][i]
        assert item["id"] == str(offer.id)
        assert item["merchant_name"] == merchant_name
        expected_cashback_type = (
            "fixed" if offer.fixed_amount is not None else "percent"
        )
        assert item["cashback_type"] == expected_cashback_type
        expected_cashback_value = (
            offer.fixed_amount if offer.fixed_amount is not None else offer.percentage
        )
        assert item["cashback_value"] == expected_cashback_value
        assert item["monthly_cap"] == offer.monthly_cap_per_user
        assert item["start_date"] == offer.start_date.isoformat()
        assert item["end_date"] == offer.end_date.isoformat()


# ──────────────────────────────────────────────────────────────────────────────
# GET /api/v1/offers/active
# ──────────────────────────────────────────────────────────────────────────────


def test_list_active_offers_returns_200_on_success(
    user_client: TestClient,
    offer_service_mock: Mock,
    offer_factory: Callable[..., Offer],
) -> None:
    # Arrange
    offer_ids = [
        "a0000001-0000-0000-0000-000000000001",
        "a0000002-0000-0000-0000-000000000002",
    ]
    merchant_names = ["Shoply", "QuickCart"]
    offers = [offer_factory(id=offer_ids[i]) for i in range(2)]
    items: list[tuple[Offer, str]] = list(zip(offers, merchant_names))
    offer_service_mock.list_active_offers.return_value = (items, 2)

    # Act
    response = user_client.get("/api/v1/offers/active")

    # Assert
    assert response.status_code == status.HTTP_200_OK
    _assert_active_offers_response(
        response.json(),
        items,
        total=2,
        page=1,
        page_size=settings.default_page_size,
    )


def test_list_active_offers_maps_fixed_cashback_correctly(
    user_client: TestClient,
    offer_service_mock: Mock,
    offer_factory: Callable[..., Offer],
) -> None:
    # Arrange
    fixed_offer = offer_factory(percentage=0.0, fixed_amount=5.0)
    merchant_name = "QuickCart"
    items: list[tuple[Offer, str]] = [(fixed_offer, merchant_name)]
    offer_service_mock.list_active_offers.return_value = (items, 1)

    # Act
    response = user_client.get("/api/v1/offers/active")

    # Assert
    assert response.status_code == status.HTTP_200_OK
    _assert_active_offers_response(
        response.json(),
        items,
        total=1,
        page=1,
        page_size=settings.default_page_size,
    )


def test_list_active_offers_returns_200_on_empty_results(
    user_client: TestClient,
    offer_service_mock: Mock,
) -> None:
    # Arrange
    offer_service_mock.list_active_offers.return_value = ([], 0)

    # Act
    response = user_client.get("/api/v1/offers/active")

    # Assert
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["total"] == 0
    assert data["offers"] == []


@pytest.mark.parametrize(
    "exception,expected_status,expected_code",
    [
        (
            Exception("Unexpected DB failure"),
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            ErrorCode.INTERNAL_SERVER_ERROR,
        ),
    ],
)
def test_list_active_offers_returns_error_on_exception(
    user_client: TestClient,
    offer_service_mock: Mock,
    exception: Exception,
    expected_status: int,
    expected_code: str,
) -> None:
    # Arrange
    offer_service_mock.list_active_offers.side_effect = exception

    # Act
    response = user_client.get("/api/v1/offers/active")

    # Assert
    assert response.status_code == expected_status
    _assert_error_code(response.json(), expected_code)


@pytest.mark.parametrize(
    "query_string",
    [
        "page=0",  # below minimum page
        "page_size=0",  # below minimum page_size
        f"page_size={settings.max_page_size + 1}",  # above maximum page_size
    ],
)
def test_list_active_offers_returns_422_on_invalid_pagination_params(
    user_client: TestClient,
    query_string: str,
) -> None:
    # Act
    response = user_client.get(f"/api/v1/offers/active?{query_string}")

    # Assert
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


@pytest.mark.parametrize(
    "query_string",
    [
        "page=1",  # minimum valid page
        "page_size=1",  # minimum valid page_size
        f"page_size={settings.default_page_size}",  # default page_size
        f"page_size={settings.max_page_size}",  # maximum valid page_size
    ],
)
def test_list_active_offers_returns_200_on_valid_pagination_params(
    user_client: TestClient,
    offer_service_mock: Mock,
    query_string: str,
) -> None:
    # Arrange
    offer_service_mock.list_active_offers.return_value = ([], 0)

    # Act
    response = user_client.get(f"/api/v1/offers/active?{query_string}")

    # Assert
    assert response.status_code == status.HTTP_200_OK
