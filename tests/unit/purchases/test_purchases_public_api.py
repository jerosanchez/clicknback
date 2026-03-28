from decimal import Decimal
from typing import Any, AsyncGenerator, Callable, Generator
from unittest.mock import AsyncMock, Mock, create_autospec

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.core.current_user import get_current_user
from app.core.database import get_async_db
from app.core.errors.codes import ErrorCode
from app.main import app
from app.purchases.composition import get_purchase_service
from app.purchases.exceptions import (
    DuplicatePurchaseException,
    InvalidPurchaseStatusException,
    MerchantInactiveException,
    MerchantNotFoundException,
    OfferNotAvailableException,
    PurchaseNotFoundException,
    PurchaseOwnershipViolationException,
    PurchaseViewForbiddenException,
    UnsupportedCurrencyException,
    UserInactiveException,
    UserNotFoundException,
)
from app.purchases.models import Purchase
from app.purchases.services import PurchaseService

# ──────────────────────────────────────────────────────────────────────────────
# Fixtures
# ──────────────────────────────────────────────────────────────────────────────


@pytest.fixture
def purchase_service_mock() -> Mock:
    return create_autospec(PurchaseService)


async def _mock_get_async_db() -> AsyncGenerator[AsyncMock, Any]:
    yield AsyncMock()


@pytest.fixture
def client(purchase_service_mock: Mock) -> Generator[TestClient, None, None]:
    app.dependency_overrides[get_async_db] = _mock_get_async_db
    app.dependency_overrides[get_purchase_service] = lambda: purchase_service_mock
    app.dependency_overrides[get_current_user] = lambda: Mock()

    test_client = TestClient(app)
    yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def unauthenticated_client(
    purchase_service_mock: Mock,
) -> Generator[TestClient, None, None]:
    """Client that does NOT override the auth dependency — auth is absent."""
    app.dependency_overrides[get_async_db] = _mock_get_async_db
    app.dependency_overrides[get_purchase_service] = lambda: purchase_service_mock

    yield TestClient(app, raise_server_exceptions=False)

    app.dependency_overrides.clear()


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────


def _ingest_input_data() -> dict[str, Any]:
    return {
        "external_id": "txn_test_001",
        "user_id": "b7e2c1a2-4f3a-4e2b-9c1a-8d2e3f4b5c6d",
        "merchant_id": "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d",
        "amount": "100.00",
        "currency": "EUR",
    }


def _assert_purchase_out_response(data: dict[str, Any], purchase: Purchase) -> None:
    assert data["id"] == purchase.id
    assert data["status"] == purchase.status
    assert Decimal(str(data["cashback_amount"])) == purchase.cashback_amount


def _assert_error_payload(data: dict[str, Any], expected_code: str) -> None:
    assert "error" in data
    assert data["error"]["code"] == expected_code


# ──────────────────────────────────────────────────────────────────────────────
# POST /api/v1/purchases — success
# ──────────────────────────────────────────────────────────────────────────────


def test_ingest_purchase_returns_201_on_success(
    client: TestClient,
    purchase_service_mock: Mock,
    purchase_factory: Callable[..., Purchase],
) -> None:
    # Arrange
    purchase = purchase_factory()
    purchase_service_mock.ingest_purchase.return_value = purchase

    # Act
    response = client.post("/api/v1/purchases", json=_ingest_input_data())

    # Assert
    assert response.status_code == status.HTTP_201_CREATED
    _assert_purchase_out_response(response.json(), purchase)


# ──────────────────────────────────────────────────────────────────────────────
# POST /api/v1/purchases — all exception → status code + error code mapping
# ──────────────────────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "exception,expected_status,expected_code",
    [
        (
            PurchaseOwnershipViolationException(
                "b7e2c1a2-4f3a-4e2b-9c1a-8d2e3f4b5c6d",
                "00000000-0000-0000-0000-000000000099",
            ),
            status.HTTP_403_FORBIDDEN,
            "FORBIDDEN",
        ),
        (
            DuplicatePurchaseException(
                "txn_test_001",
                __import__("datetime").datetime(2026, 3, 1),
                Decimal("100"),
            ),
            status.HTTP_409_CONFLICT,
            "DUPLICATE_PURCHASE",
        ),
        (
            UserNotFoundException("uid-001"),
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            "USER_NOT_ELIGIBLE",
        ),
        (
            UserInactiveException("uid-001"),
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            "USER_NOT_ELIGIBLE",
        ),
        (
            MerchantNotFoundException("mid-001"),
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            "MERCHANT_NOT_ELIGIBLE",
        ),
        (
            MerchantInactiveException("mid-001"),
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            "MERCHANT_NOT_ELIGIBLE",
        ),
        (
            OfferNotAvailableException("mid-001"),
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            "OFFER_NOT_AVAILABLE",
        ),
        (
            UnsupportedCurrencyException("USD"),
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            "UNSUPPORTED_CURRENCY",
        ),
        (
            Exception("unexpected failure"),
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            ErrorCode.INTERNAL_SERVER_ERROR,
        ),
    ],
)
def test_ingest_purchase_returns_error_on_exception(
    client: TestClient,
    purchase_service_mock: Mock,
    exception: Exception,
    expected_status: int,
    expected_code: str,
) -> None:
    # Arrange
    purchase_service_mock.ingest_purchase.side_effect = exception

    # Act
    response = client.post("/api/v1/purchases", json=_ingest_input_data())

    # Assert
    assert response.status_code == expected_status
    _assert_error_payload(response.json(), expected_code)


# ──────────────────────────────────────────────────────────────────────────────
# POST /api/v1/purchases — full error detail shape per domain exception
# ──────────────────────────────────────────────────────────────────────────────


def test_ingest_purchase_returns_403_with_details_on_ownership_violation(
    client: TestClient,
    purchase_service_mock: Mock,
) -> None:
    # Arrange
    current_user_id = "b7e2c1a2-4f3a-4e2b-9c1a-8d2e3f4b5c6d"
    other_user_id = "00000000-0000-0000-0000-000000000099"
    exc = PurchaseOwnershipViolationException(current_user_id, other_user_id)
    purchase_service_mock.ingest_purchase.side_effect = exc

    # Act
    response = client.post("/api/v1/purchases", json=_ingest_input_data())

    # Assert
    assert response.status_code == status.HTTP_403_FORBIDDEN
    error = response.json()["error"]
    assert error["code"] == "FORBIDDEN"
    assert error["message"] == "You can only ingest purchases on your own behalf."
    assert "reason" in error["details"]


def test_ingest_purchase_returns_409_with_details_on_duplicate(
    client: TestClient,
    purchase_service_mock: Mock,
) -> None:
    # Arrange
    import datetime

    external_id = "txn_test_001"
    created_at = datetime.datetime(2026, 3, 1, 10, 0, 0)
    amount = Decimal("100.00")
    exc = DuplicatePurchaseException(external_id, created_at, amount)
    purchase_service_mock.ingest_purchase.side_effect = exc

    # Act
    response = client.post("/api/v1/purchases", json=_ingest_input_data())

    # Assert
    assert response.status_code == status.HTTP_409_CONFLICT
    error = response.json()["error"]
    assert error["code"] == "DUPLICATE_PURCHASE"
    assert external_id in error["message"]
    assert error["details"]["external_id"] == external_id
    assert error["details"]["previously_processed_amount"] == str(amount)
    assert "previously_created_at" in error["details"]
    assert "action" in error["details"]


def test_ingest_purchase_returns_422_with_details_on_user_not_found(
    client: TestClient,
    purchase_service_mock: Mock,
) -> None:
    # Arrange
    user_id = "00000000-0000-0000-0000-000000000001"
    exc = UserNotFoundException(user_id)
    purchase_service_mock.ingest_purchase.side_effect = exc

    # Act
    response = client.post("/api/v1/purchases", json=_ingest_input_data())

    # Assert
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    error = response.json()["error"]
    assert error["code"] == "USER_NOT_ELIGIBLE"
    assert error["message"] == "User is not eligible to ingest purchases."
    assert error["details"]["user_id"] == user_id
    assert "reason" in error["details"]


def test_ingest_purchase_returns_422_with_details_on_user_inactive(
    client: TestClient,
    purchase_service_mock: Mock,
) -> None:
    # Arrange
    user_id = "b7e2c1a2-4f3a-4e2b-9c1a-8d2e3f4b5c6d"
    exc = UserInactiveException(user_id)
    purchase_service_mock.ingest_purchase.side_effect = exc

    # Act
    response = client.post("/api/v1/purchases", json=_ingest_input_data())

    # Assert
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    error = response.json()["error"]
    assert error["code"] == "USER_NOT_ELIGIBLE"
    assert error["message"] == "User is not eligible to ingest purchases."
    assert error["details"]["user_id"] == user_id


def test_ingest_purchase_returns_422_with_details_on_merchant_not_found(
    client: TestClient,
    purchase_service_mock: Mock,
) -> None:
    # Arrange
    merchant_id = "00000000-0000-0000-0000-000000000002"
    exc = MerchantNotFoundException(merchant_id)
    purchase_service_mock.ingest_purchase.side_effect = exc

    # Act
    response = client.post("/api/v1/purchases", json=_ingest_input_data())

    # Assert
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    error = response.json()["error"]
    assert error["code"] == "MERCHANT_NOT_ELIGIBLE"
    assert error["message"] == "Merchant is not eligible to process purchases."
    assert error["details"]["merchant_id"] == merchant_id
    assert "reason" in error["details"]


def test_ingest_purchase_returns_422_with_details_on_merchant_inactive(
    client: TestClient,
    purchase_service_mock: Mock,
) -> None:
    # Arrange
    merchant_id = "a5b6c7d8-e9f0-4a1b-2c3d-4e5f6a7b8c9d"
    exc = MerchantInactiveException(merchant_id)
    purchase_service_mock.ingest_purchase.side_effect = exc

    # Act
    response = client.post("/api/v1/purchases", json=_ingest_input_data())

    # Assert
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    error = response.json()["error"]
    assert error["code"] == "MERCHANT_NOT_ELIGIBLE"
    assert error["message"] == "Merchant is not eligible to process purchases."
    assert error["details"]["merchant_id"] == merchant_id


def test_ingest_purchase_returns_422_with_details_on_offer_not_available(
    client: TestClient,
    purchase_service_mock: Mock,
) -> None:
    # Arrange
    merchant_id = "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d"
    exc = OfferNotAvailableException(merchant_id)
    purchase_service_mock.ingest_purchase.side_effect = exc

    # Act
    response = client.post("/api/v1/purchases", json=_ingest_input_data())

    # Assert
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    error = response.json()["error"]
    assert error["code"] == "OFFER_NOT_AVAILABLE"
    assert merchant_id in error["message"]
    assert error["details"]["merchant_id"] == merchant_id
    assert "reason" in error["details"]


def test_ingest_purchase_returns_422_with_details_on_unsupported_currency(
    client: TestClient,
    purchase_service_mock: Mock,
) -> None:
    # Arrange
    currency = "USD"
    exc = UnsupportedCurrencyException(currency)
    purchase_service_mock.ingest_purchase.side_effect = exc

    # Act
    response = client.post("/api/v1/purchases", json=_ingest_input_data())

    # Assert
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    error = response.json()["error"]
    assert error["code"] == "UNSUPPORTED_CURRENCY"
    assert currency in error["message"]
    assert error["details"]["currency"] == currency
    assert "reason" in error["details"]


# ──────────────────────────────────────────────────────────────────────────────
# POST /api/v1/purchases — request body validation (422 from Pydantic)
# ──────────────────────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "invalid_body,description",
    [
        (
            {k: v for k, v in _ingest_input_data().items() if k != "external_id"},
            "missing external_id",
        ),
        (
            {**_ingest_input_data(), "external_id": ""},
            "empty external_id",
        ),
        (
            {k: v for k, v in _ingest_input_data().items() if k != "amount"},
            "missing amount",
        ),
        (
            {**_ingest_input_data(), "amount": "-1.00"},
            "negative amount",
        ),
        (
            {**_ingest_input_data(), "amount": "0"},
            "zero amount",
        ),
        (
            {**_ingest_input_data(), "user_id": "not-a-uuid"},
            "invalid user_id UUID",
        ),
        (
            {**_ingest_input_data(), "merchant_id": "not-a-uuid"},
            "invalid merchant_id UUID",
        ),
        (
            {**_ingest_input_data(), "currency": "EU"},
            "currency too short",
        ),
        (
            {**_ingest_input_data(), "currency": "EURO"},
            "currency too long",
        ),
    ],
)
def test_ingest_purchase_returns_422_on_invalid_request_body(
    client: TestClient,
    invalid_body: dict[str, Any],
    description: str,
) -> None:
    # Act
    response = client.post("/api/v1/purchases", json=invalid_body)

    # Assert
    assert (
        response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    ), f"Expected 422 for: {description}"


# ──────────────────────────────────────────────────────────────────────────────
# POST /api/v1/purchases — authentication
# ──────────────────────────────────────────────────────────────────────────────


def test_ingest_purchase_returns_401_on_missing_auth(
    unauthenticated_client: TestClient,
) -> None:
    # Act
    response = unauthenticated_client.post(
        "/api/v1/purchases", json=_ingest_input_data()
    )

    # Assert
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


# ──────────────────────────────────────────────────────────────────────────────
# GET /api/v1/purchases/{purchase_id} — helpers
# ──────────────────────────────────────────────────────────────────────────────

# Used for purchase details tests (GET /api/v1/purchases/{purchase_id})
_PURCHASE_ID = "aa000001-0000-0000-0000-000000000001"
_MERCHANT_NAME_DETAILS = "Shoply"


def _assert_purchase_details_response(
    data: dict[str, Any], purchase: Purchase, merchant_name: str
) -> None:
    assert data["id"] == purchase.id
    assert data["merchant_name"] == merchant_name
    assert Decimal(str(data["amount"])) == purchase.amount
    assert data["status"] == purchase.status
    assert Decimal(str(data["cashback_amount"])) == purchase.cashback_amount
    assert data["cashback_status"] is None
    assert "created_at" in data


# ──────────────────────────────────────────────────────────────────────────────
# GET /api/v1/purchases/{purchase_id} — success
# ──────────────────────────────────────────────────────────────────────────────


def test_get_purchase_details_returns_200_on_success(
    client: TestClient,
    purchase_service_mock: Mock,
    purchase_factory: Callable[..., Purchase],
) -> None:
    # Arrange
    purchase = purchase_factory(id=_PURCHASE_ID)
    purchase_service_mock.get_purchase_details.return_value = (
        purchase,
        _MERCHANT_NAME_DETAILS,
    )

    # Act
    response = client.get(f"/api/v1/purchases/{_PURCHASE_ID}")

    # Assert
    assert response.status_code == status.HTTP_200_OK
    _assert_purchase_details_response(response.json(), purchase, _MERCHANT_NAME_DETAILS)


# ──────────────────────────────────────────────────────────────────────────────
# GET /api/v1/purchases/{purchase_id} — all exceptions → status code + error code
# ──────────────────────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "exception,expected_status,expected_code",
    [
        (
            PurchaseNotFoundException(_PURCHASE_ID),
            status.HTTP_404_NOT_FOUND,
            ErrorCode.NOT_FOUND,
        ),
        (
            PurchaseViewForbiddenException(
                _PURCHASE_ID,
                "c8d3e2b1-5a4b-4c3d-8b2a-7e6f5d4c3b2a",
                "b7e2c1a2-4f3a-4e2b-9c1a-8d2e3f4b5c6d",
            ),
            status.HTTP_403_FORBIDDEN,
            ErrorCode.FORBIDDEN,
        ),
        (
            Exception("unexpected failure"),
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            ErrorCode.INTERNAL_SERVER_ERROR,
        ),
    ],
)
def test_get_purchase_details_returns_error_on_exception(
    client: TestClient,
    purchase_service_mock: Mock,
    exception: Exception,
    expected_status: int,
    expected_code: str,
) -> None:
    # Arrange
    purchase_service_mock.get_purchase_details.side_effect = exception

    # Act
    response = client.get(f"/api/v1/purchases/{_PURCHASE_ID}")

    # Assert
    assert response.status_code == expected_status
    _assert_error_payload(response.json(), expected_code)


# ──────────────────────────────────────────────────────────────────────────────
# GET /api/v1/purchases/{purchase_id} — full error detail shape per exception
# ──────────────────────────────────────────────────────────────────────────────


def test_get_purchase_details_returns_404_with_details_on_not_found(
    client: TestClient,
    purchase_service_mock: Mock,
) -> None:
    # Arrange
    purchase_service_mock.get_purchase_details.side_effect = PurchaseNotFoundException(
        _PURCHASE_ID
    )

    # Act
    response = client.get(f"/api/v1/purchases/{_PURCHASE_ID}")

    # Assert
    assert response.status_code == status.HTTP_404_NOT_FOUND
    error = response.json()["error"]
    assert error["code"] == ErrorCode.NOT_FOUND
    assert _PURCHASE_ID in error["message"]
    assert error["details"]["resource_type"] == "purchase"
    assert error["details"]["resource_id"] == _PURCHASE_ID


def test_get_purchase_details_returns_403_with_details_on_forbidden(
    client: TestClient,
    purchase_service_mock: Mock,
) -> None:
    # Arrange
    owner_id = "c8d3e2b1-5a4b-4c3d-8b2a-7e6f5d4c3b2a"
    current_id = "b7e2c1a2-4f3a-4e2b-9c1a-8d2e3f4b5c6d"
    exc = PurchaseViewForbiddenException(_PURCHASE_ID, owner_id, current_id)
    purchase_service_mock.get_purchase_details.side_effect = exc

    # Act
    response = client.get(f"/api/v1/purchases/{_PURCHASE_ID}")

    # Assert
    assert response.status_code == status.HTTP_403_FORBIDDEN
    error = response.json()["error"]
    assert error["code"] == ErrorCode.FORBIDDEN
    assert "another user" in error["message"]
    assert error["details"]["purchase_id"] == _PURCHASE_ID
    assert error["details"]["resource_owner"] == owner_id
    assert error["details"]["current_user"] == current_id


# ──────────────────────────────────────────────────────────────────────────────
# GET /api/v1/users/me/purchases — success
# ──────────────────────────────────────────────────────────────────────────────

# Used for user purchases listing tests (GET /api/v1/users/me/purchases)
_MERCHANT_ID = "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d"
_MERCHANT_NAME_LIST = "Shoply"


def test_list_user_purchases_returns_200_with_paginated_items(
    client: TestClient,
    purchase_service_mock: Mock,
    purchase_factory: Callable[..., Purchase],
) -> None:
    # Arrange
    purchase = purchase_factory(merchant_id=_MERCHANT_ID)
    purchase_service_mock.list_user_purchases.return_value = (
        [(purchase, _MERCHANT_NAME_LIST)],
        1,
    )

    # Act
    response = client.get("/api/v1/users/me/purchases")

    # Assert
    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert body["total"] == 1
    assert body["page"] == 1
    assert body["page_size"] == 10
    assert len(body["items"]) == 1
    item = body["items"][0]
    assert item["id"] == purchase.id
    assert item["merchant_name"] == _MERCHANT_NAME_LIST
    assert item["status"] == purchase.status


def test_list_user_purchases_returns_empty_list(
    client: TestClient,
    purchase_service_mock: Mock,
) -> None:
    # Arrange
    purchase_service_mock.list_user_purchases.return_value = ([], 0)

    # Act
    response = client.get("/api/v1/users/me/purchases")

    # Assert
    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert body["total"] == 0
    assert body["items"] == []


def test_list_user_purchases_passes_pagination_params_to_service(
    client: TestClient,
    purchase_service_mock: Mock,
) -> None:
    # Arrange
    purchase_service_mock.list_user_purchases.return_value = ([], 0)

    # Act
    response = client.get("/api/v1/users/me/purchases?page=2&page_size=5")

    # Assert
    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert body["page"] == 2
    assert body["page_size"] == 5
    call_kwargs = purchase_service_mock.list_user_purchases.call_args[1]
    assert call_kwargs["page"] == 2
    assert call_kwargs["page_size"] == 5


def test_list_user_purchases_passes_status_filter_to_service(
    client: TestClient,
    purchase_service_mock: Mock,
    purchase_factory: Callable[..., Purchase],
) -> None:
    # Arrange
    purchase = purchase_factory(status="confirmed")
    purchase_service_mock.list_user_purchases.return_value = (
        [(purchase, _MERCHANT_NAME_LIST)],
        1,
    )

    # Act
    response = client.get("/api/v1/users/me/purchases?status=confirmed")

    # Assert
    assert response.status_code == status.HTTP_200_OK
    call_kwargs = purchase_service_mock.list_user_purchases.call_args[1]
    assert call_kwargs["status"] == "confirmed"


# ──────────────────────────────────────────────────────────────────────────────
# GET /api/v1/users/me/purchases — failure responses
# ──────────────────────────────────────────────────────────────────────────────


def test_list_user_purchases_returns_500_on_unexpected_error(
    client: TestClient,
    purchase_service_mock: Mock,
) -> None:
    # Arrange
    purchase_service_mock.list_user_purchases.side_effect = RuntimeError(
        "database exploded"
    )

    # Act
    response = client.get("/api/v1/users/me/purchases")

    # Assert
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    _assert_error_payload(response.json(), ErrorCode.INTERNAL_SERVER_ERROR)


def test_list_user_purchases_returns_401_when_unauthenticated(
    unauthenticated_client: TestClient,
) -> None:
    response = unauthenticated_client.get("/api/v1/users/me/purchases")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_list_user_purchases_returns_422_on_invalid_status(
    client: TestClient,
    purchase_service_mock: Mock,
) -> None:
    # Arrange
    purchase_service_mock.list_user_purchases.side_effect = (
        InvalidPurchaseStatusException("bad_status")
    )

    # Act
    response = client.get("/api/v1/users/me/purchases?status=bad_status")

    # Assert
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response.json()["error"]["code"] == "INVALID_PURCHASE_STATUS"


def test_list_user_purchases_returns_422_on_invalid_page_param(
    client: TestClient,
    purchase_service_mock: Mock,
) -> None:
    # FastAPI validates Query params before the handler runs; page must be >= 1
    response = client.get("/api/v1/users/me/purchases?page=0")
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
