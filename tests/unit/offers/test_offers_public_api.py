from typing import Any, AsyncGenerator, Callable, Generator
from unittest.mock import AsyncMock, Mock, create_autospec

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.auth.exceptions import InvalidTokenException
from app.core.config import settings
from app.core.current_user import get_current_user
from app.core.database import get_async_db
from app.core.errors.codes import ErrorCode
from app.main import app
from app.offers.composition import get_offer_service
from app.offers.exceptions import (
    InactiveMerchantForOfferException,
    InactiveOfferException,
    OfferNotFoundException,
)
from app.offers.models import Offer
from app.offers.services import OfferService
from app.users.models import UserRoleEnum


@pytest.fixture
def offer_service_mock() -> Mock:
    return create_autospec(OfferService)


async def _mock_get_async_db() -> AsyncGenerator[AsyncMock, Any]:
    yield AsyncMock()


@pytest.fixture
def user_client(offer_service_mock: Mock) -> Generator[TestClient, None, None]:
    app.dependency_overrides[get_async_db] = _mock_get_async_db
    app.dependency_overrides[get_offer_service] = lambda: offer_service_mock
    app.dependency_overrides[get_current_user] = lambda: Mock(role=UserRoleEnum.user)

    yield TestClient(app)

    app.dependency_overrides.clear()


@pytest.fixture
def admin_client(offer_service_mock: Mock) -> Generator[TestClient, None, None]:
    app.dependency_overrides[get_async_db] = _mock_get_async_db
    app.dependency_overrides[get_offer_service] = lambda: offer_service_mock
    app.dependency_overrides[get_current_user] = lambda: Mock(role=UserRoleEnum.admin)

    yield TestClient(app)

    app.dependency_overrides.clear()


@pytest.fixture
def unauthenticated_client(
    offer_service_mock: Mock,
) -> Generator[TestClient, None, None]:
    def raise_invalid_token() -> None:
        raise InvalidTokenException()

    app.dependency_overrides[get_async_db] = _mock_get_async_db
    app.dependency_overrides[get_offer_service] = lambda: offer_service_mock
    app.dependency_overrides[get_current_user] = raise_invalid_token

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


# ──────────────────────────────────────────────────────────────────────────────
# GET /api/v1/offers/{offer_id}
# ──────────────────────────────────────────────────────────────────────────────

_ACTIVE_OFFER_ID = "f0e1d2c3-b4a5-4678-9012-3456789abcde"
_MISSING_OFFER_ID = "00000000-0000-0000-0000-000000000000"


def _assert_offer_details_response(
    data: dict[str, Any], offer: Offer, merchant_name: str
) -> None:
    assert data["id"] == str(offer.id)
    assert data["merchant_name"] == merchant_name
    expected_cashback_type = "fixed" if offer.fixed_amount is not None else "percent"
    assert data["cashback_type"] == expected_cashback_type
    expected_cashback_value = (
        offer.fixed_amount if offer.fixed_amount is not None else offer.percentage
    )
    assert data["cashback_value"] == expected_cashback_value
    assert data["monthly_cap"] == offer.monthly_cap_per_user
    assert data["start_date"] == offer.start_date.isoformat()
    assert data["end_date"] == offer.end_date.isoformat()
    assert data["status"] == ("active" if offer.active else "inactive")


def test_get_offer_details_returns_200_on_success(
    user_client: TestClient,
    offer_service_mock: Mock,
    offer_factory: Callable[..., Offer],
) -> None:
    # Arrange
    offer = offer_factory(id=_ACTIVE_OFFER_ID, active=True)
    merchant_name = "Shoply"
    offer_service_mock.get_offer_details.return_value = (offer, merchant_name)

    # Act
    response = user_client.get(f"/api/v1/offers/{_ACTIVE_OFFER_ID}")

    # Assert
    assert response.status_code == status.HTTP_200_OK
    _assert_offer_details_response(response.json(), offer, merchant_name)


def test_get_offer_details_maps_fixed_cashback_correctly(
    user_client: TestClient,
    offer_service_mock: Mock,
    offer_factory: Callable[..., Offer],
) -> None:
    # Arrange
    fixed_offer = offer_factory(
        id=_ACTIVE_OFFER_ID, percentage=0.0, fixed_amount=5.0, active=True
    )
    merchant_name = "QuickCart"
    offer_service_mock.get_offer_details.return_value = (fixed_offer, merchant_name)

    # Act
    response = user_client.get(f"/api/v1/offers/{_ACTIVE_OFFER_ID}")

    # Assert
    assert response.status_code == status.HTTP_200_OK
    _assert_offer_details_response(response.json(), fixed_offer, merchant_name)


def test_get_offer_details_admin_returns_200_on_inactive_offer(
    admin_client: TestClient,
    offer_service_mock: Mock,
    offer_factory: Callable[..., Offer],
) -> None:
    # Arrange
    inactive_offer = offer_factory(id=_ACTIVE_OFFER_ID, active=False)
    merchant_name = "UrbanMart"
    offer_service_mock.get_offer_details.return_value = (inactive_offer, merchant_name)

    # Act
    response = admin_client.get(f"/api/v1/offers/{_ACTIVE_OFFER_ID}")

    # Assert
    assert response.status_code == status.HTTP_200_OK
    _assert_offer_details_response(response.json(), inactive_offer, merchant_name)


def test_get_offer_details_returns_401_on_unauthenticated_request(
    unauthenticated_client: TestClient,
) -> None:
    # Act
    response = unauthenticated_client.get(f"/api/v1/offers/{_ACTIVE_OFFER_ID}")

    # Assert
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    _assert_error_code(response.json(), ErrorCode.INVALID_TOKEN)


def test_get_offer_details_returns_404_on_offer_not_found(
    user_client: TestClient,
    offer_service_mock: Mock,
) -> None:
    # Arrange
    offer_service_mock.get_offer_details.side_effect = OfferNotFoundException(
        _MISSING_OFFER_ID
    )

    # Act
    response = user_client.get(f"/api/v1/offers/{_MISSING_OFFER_ID}")

    # Assert
    assert response.status_code == status.HTTP_404_NOT_FOUND
    data = response.json()
    _assert_error_code(data, ErrorCode.NOT_FOUND)
    assert data["error"]["details"]["resource_type"] == "offer"
    assert data["error"]["details"]["resource_id"] == _MISSING_OFFER_ID


def test_get_offer_details_returns_403_on_inactive_offer_for_non_admin(
    user_client: TestClient,
    offer_service_mock: Mock,
) -> None:
    # Arrange
    inactive_offer_id = "b2c3d4e5-f6a7-4890-abcd-ef1234567890"
    offer_service_mock.get_offer_details.side_effect = InactiveOfferException(
        inactive_offer_id
    )

    # Act
    response = user_client.get(f"/api/v1/offers/{inactive_offer_id}")

    # Assert
    assert response.status_code == status.HTTP_403_FORBIDDEN
    data = response.json()
    _assert_error_code(data, ErrorCode.FORBIDDEN)
    assert data["error"]["details"]["resource_type"] == "offer"
    assert data["error"]["details"]["resource_id"] == inactive_offer_id


def test_get_offer_details_returns_403_on_inactive_merchant_for_non_admin(
    user_client: TestClient,
    offer_service_mock: Mock,
) -> None:
    # Arrange
    offer_id = "d0000001-0000-0000-0000-000000000001"
    merchant_id = "a5b6c7d8-e9f0-4a1b-2c3d-4e5f6a7b8c9d"
    offer_service_mock.get_offer_details.side_effect = (
        InactiveMerchantForOfferException(offer_id, merchant_id)
    )

    # Act
    response = user_client.get(f"/api/v1/offers/{offer_id}")

    # Assert
    assert response.status_code == status.HTTP_403_FORBIDDEN
    data = response.json()
    _assert_error_code(data, ErrorCode.FORBIDDEN)
    assert data["error"]["details"]["resource_type"] == "offer"
    assert data["error"]["details"]["resource_id"] == offer_id


def test_get_offer_details_returns_500_on_unexpected_error(
    user_client: TestClient,
    offer_service_mock: Mock,
) -> None:
    # Arrange
    offer_service_mock.get_offer_details.side_effect = Exception("DB connection lost")

    # Act
    response = user_client.get(f"/api/v1/offers/{_ACTIVE_OFFER_ID}")

    # Assert
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    _assert_error_code(response.json(), ErrorCode.INTERNAL_SERVER_ERROR)
