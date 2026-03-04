from typing import Any, Callable, Generator
from unittest.mock import Mock, create_autospec

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.core.config import settings
from app.core.current_user import get_current_admin_user, get_current_user
from app.core.database import get_db
from app.core.errors.builders import forbidden_error
from app.core.errors.codes import ErrorCode
from app.main import app
from app.merchants.exceptions import MerchantNotFoundException
from app.offers.composition import get_offer_service
from app.offers.errors import ErrorCode as OfferErrorCode
from app.offers.exceptions import (
    ActiveOfferAlreadyExistsException,
    InvalidCashbackValueException,
    InvalidDateRangeException,
    InvalidMonthlyCapException,
    MerchantNotActiveException,
    PastOfferStartDateException,
)
from app.offers.models import Offer
from app.offers.services import OfferService


@pytest.fixture
def offer_service_mock() -> Mock:
    return create_autospec(OfferService)


@pytest.fixture
def client(offer_service_mock: Mock) -> Generator[TestClient, None, None]:
    def mock_get_db() -> Generator[Mock, None, None]:
        yield Mock()

    app.dependency_overrides[get_db] = mock_get_db
    app.dependency_overrides[get_offer_service] = lambda: offer_service_mock
    app.dependency_overrides[get_current_admin_user] = lambda: Mock()

    yield TestClient(app)

    app.dependency_overrides.clear()


@pytest.fixture
def non_admin_client(
    offer_service_mock: Mock,
) -> Generator[TestClient, None, None]:
    def mock_get_db() -> Generator[Mock, None, None]:
        yield Mock()

    def raise_forbidden() -> None:
        raise forbidden_error("Admin access required.", {})

    app.dependency_overrides[get_db] = mock_get_db
    app.dependency_overrides[get_offer_service] = lambda: offer_service_mock
    app.dependency_overrides[get_current_admin_user] = raise_forbidden

    yield TestClient(app)

    app.dependency_overrides.clear()


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


def _assert_offer_out_response(data: dict[str, Any], offer: Offer) -> None:
    assert data["id"] == str(offer.id)
    assert data["merchant_id"] == str(offer.merchant_id)
    expected_cashback_type = "fixed" if offer.fixed_amount is not None else "percent"
    assert data["cashback_type"] == expected_cashback_type
    expected_cashback_value = (
        offer.fixed_amount if offer.fixed_amount is not None else offer.percentage
    )
    assert data["cashback_value"] == expected_cashback_value
    assert data["status"] == ("active" if offer.active else "inactive")


def _assert_paginated_offers_response(
    data: dict[str, Any],
    items: list[Offer],
    total: int,
    page: int,
    page_size: int,
) -> None:
    assert data["total"] == total
    assert data["page"] == page
    assert data["page_size"] == page_size
    assert len(data["items"]) == len(items)
    for i, offer in enumerate(items):
        item = data["items"][i]
        assert item["id"] == str(offer.id)
        assert item["merchant_id"] == str(offer.merchant_id)
        expected_cashback_type = (
            "fixed" if offer.fixed_amount is not None else "percent"
        )
        assert item["cashback_type"] == expected_cashback_type
        expected_cashback_value = (
            offer.fixed_amount if offer.fixed_amount is not None else offer.percentage
        )
        assert item["cashback_value"] == expected_cashback_value
        assert item["start_date"] == offer.start_date.isoformat()
        assert item["end_date"] == offer.end_date.isoformat()
        assert item["monthly_cap_per_user"] == offer.monthly_cap_per_user
        assert item["status"] == ("active" if offer.active else "inactive")


# ──────────────────────────────────────────────────────────────────────────────
# POST /api/v1/offers
# ──────────────────────────────────────────────────────────────────────────────


def test_create_offer_returns_201_on_success(
    client: TestClient,
    offer_service_mock: Mock,
    offer_factory: Callable[..., Offer],
    offer_input_data: Callable[[Offer], dict[str, Any]],
) -> None:
    # Arrange
    offer = offer_factory()
    offer_service_mock.create_offer.return_value = offer
    request_data = offer_input_data(offer)

    # Act
    response = client.post("/api/v1/offers", json=request_data)

    # Assert
    assert response.status_code == status.HTTP_201_CREATED
    _assert_offer_out_response(response.json(), offer)


def test_create_offer_enforces_admin_user(
    non_admin_client: TestClient,
    offer_factory: Callable[..., Offer],
    offer_input_data: Callable[[Offer], dict[str, Any]],
) -> None:
    # Act
    response = non_admin_client.post(
        "/api/v1/offers", json=offer_input_data(offer_factory())
    )

    # Assert
    assert response.status_code == status.HTTP_403_FORBIDDEN
    _assert_error_code(response.json(), ErrorCode.FORBIDDEN)


@pytest.mark.parametrize(
    "exception,expected_status,expected_code",
    [
        (
            InvalidCashbackValueException("percent", 150.0, "Must be <= 100."),
            status.HTTP_400_BAD_REQUEST,
            ErrorCode.VALIDATION_ERROR,
        ),
        (
            PastOfferStartDateException(
                __import__("datetime").date(2025, 1, 1),
            ),
            status.HTTP_400_BAD_REQUEST,
            ErrorCode.VALIDATION_ERROR,
        ),
        (
            InvalidDateRangeException(
                __import__("datetime").date(2026, 12, 31),
                __import__("datetime").date(2026, 6, 1),
            ),
            status.HTTP_400_BAD_REQUEST,
            ErrorCode.VALIDATION_ERROR,
        ),
        (
            InvalidMonthlyCapException(0.0),
            status.HTTP_400_BAD_REQUEST,
            ErrorCode.VALIDATION_ERROR,
        ),
        (
            MerchantNotFoundException("00000000-0000-0000-0000-000000000000"),
            status.HTTP_404_NOT_FOUND,
            ErrorCode.NOT_FOUND,
        ),
        (
            MerchantNotActiveException("a1b2c3d4-e5f6-7890-abcd-ef1234567890"),
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            OfferErrorCode.MERCHANT_NOT_ACTIVE,
        ),
        (
            ActiveOfferAlreadyExistsException("a1b2c3d4-e5f6-7890-abcd-ef1234567890"),
            status.HTTP_409_CONFLICT,
            OfferErrorCode.ACTIVE_OFFER_ALREADY_EXISTS,
        ),
        (
            Exception("Unexpected DB failure"),
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            ErrorCode.INTERNAL_SERVER_ERROR,
        ),
    ],
)
def test_create_offer_returns_error_on_exception(
    client: TestClient,
    offer_service_mock: Mock,
    offer_factory: Callable[..., Offer],
    offer_input_data: Callable[[Offer], dict[str, Any]],
    exception: Exception,
    expected_status: int,
    expected_code: str,
) -> None:
    # Arrange
    offer_service_mock.create_offer.side_effect = exception

    # Act
    response = client.post("/api/v1/offers", json=offer_input_data(offer_factory()))

    # Assert
    assert response.status_code == expected_status
    _assert_error_code(response.json(), expected_code)


def test_create_offer_response_maps_all_fields_correctly(
    client: TestClient,
    offer_service_mock: Mock,
    offer_factory: Callable[..., Offer],
    offer_input_data: Callable[[Offer], dict[str, Any]],
) -> None:
    """Verify the full ORM→schema field mapping for a non-default offer
    (inactive, percentage-based) to cover all derived fields."""
    # Arrange
    inactive_offer = offer_factory(active=False)
    offer_service_mock.create_offer.return_value = inactive_offer

    # Act
    response = client.post("/api/v1/offers", json=offer_input_data(inactive_offer))

    # Assert
    assert response.status_code == status.HTTP_201_CREATED
    _assert_offer_out_response(response.json(), inactive_offer)


# ──────────────────────────────────────────────────────────────────────────────
# GET /api/v1/offers
# ──────────────────────────────────────────────────────────────────────────────


def test_list_offers_returns_200_on_success(
    client: TestClient,
    offer_service_mock: Mock,
    offer_factory: Callable[..., Offer],
) -> None:
    # Arrange
    offer_ids = [
        "a0000001-0000-0000-0000-000000000001",
        "a0000002-0000-0000-0000-000000000002",
        "a0000003-0000-0000-0000-000000000003",
    ]
    offers = [offer_factory(id=offer_ids[i]) for i in range(3)]
    offer_service_mock.list_offers.return_value = (offers, 3)

    # Act
    response = client.get("/api/v1/offers")

    # Assert
    assert response.status_code == status.HTTP_200_OK
    _assert_paginated_offers_response(
        response.json(), offers, total=3, page=1, page_size=settings.default_page_size
    )


def test_list_offers_returns_200_on_empty_results(
    client: TestClient,
    offer_service_mock: Mock,
) -> None:
    # Arrange
    offer_service_mock.list_offers.return_value = ([], 0)

    # Act
    response = client.get("/api/v1/offers")

    # Assert
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["total"] == 0
    assert data["items"] == []


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
def test_list_offers_returns_error_on_exception(
    client: TestClient,
    offer_service_mock: Mock,
    exception: Exception,
    expected_status: int,
    expected_code: str,
) -> None:
    # Arrange
    offer_service_mock.list_offers.side_effect = exception

    # Act
    response = client.get("/api/v1/offers")

    # Assert
    assert response.status_code == expected_status
    _assert_error_code(response.json(), expected_code)


def test_list_offers_enforces_admin_user(
    non_admin_client: TestClient,
) -> None:
    # Act
    response = non_admin_client.get("/api/v1/offers")

    # Assert
    assert response.status_code == status.HTTP_403_FORBIDDEN
    _assert_error_code(response.json(), ErrorCode.FORBIDDEN)


@pytest.mark.parametrize(
    "query_string",
    [
        "page=0",  # below minimum page
        "page_size=0",  # below minimum page_size
        f"page_size={settings.max_page_size + 1}",  # above maximum page_size
    ],
)
def test_list_offers_returns_422_on_invalid_pagination_params(
    client: TestClient,
    query_string: str,
) -> None:
    # Act
    response = client.get(f"/api/v1/offers?{query_string}")

    # Assert
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


@pytest.mark.parametrize(
    "query_string",
    [
        "page=1",  # minimum page
        "page_size=1",  # minimum page_size
        f"page_size={settings.default_page_size}",  # default page_size
        f"page_size={settings.max_page_size}",  # maximum page_size
    ],
)
def test_list_offers_returns_200_on_valid_pagination_params(
    client: TestClient,
    offer_service_mock: Mock,
    query_string: str,
) -> None:
    # Arrange
    offer_service_mock.list_offers.return_value = ([], 0)

    # Act
    response = client.get(f"/api/v1/offers?{query_string}")

    # Assert
    assert response.status_code == status.HTTP_200_OK


def test_list_offers_returns_400_on_invalid_status_filter(
    client: TestClient,
) -> None:
    # Arrange
    invalid_status_value = "unknown_status"

    # Act
    response = client.get(f"/api/v1/offers?status={invalid_status_value}")

    # Assert
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data = response.json()
    _assert_error_code(data, ErrorCode.VALIDATION_ERROR)
    violations = data["error"]["details"]["violations"]
    assert any(v["field"] == "status" for v in violations)


def test_list_offers_returns_400_on_inverted_date_range(
    client: TestClient,
) -> None:
    # Arrange
    date_from = "2026-12-31"
    date_to = "2026-01-01"

    # Act
    response = client.get(f"/api/v1/offers?date_from={date_from}&date_to={date_to}")

    # Assert
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data = response.json()
    _assert_error_code(data, ErrorCode.VALIDATION_ERROR)
    violations = data["error"]["details"]["violations"]
    assert any(v["field"] == "date_from" for v in violations)


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
