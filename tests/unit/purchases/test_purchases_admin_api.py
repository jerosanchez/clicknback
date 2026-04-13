from decimal import Decimal
from typing import Any, AsyncGenerator, Callable, Generator
from unittest.mock import AsyncMock, Mock, create_autospec

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.auth.exceptions import InvalidTokenException
from app.core.current_user import get_current_admin_user
from app.core.database import get_async_db
from app.core.errors.codes import ErrorCode
from app.core.unit_of_work import UnitOfWorkABC
from app.main import app
from app.purchases.composition import get_purchase_service, get_unit_of_work
from app.purchases.errors import ErrorCode as PurchaseErrorCode
from app.purchases.exceptions import (
    InvalidPurchaseStatusException,
    PurchaseAlreadyReversedException,
    PurchaseNotFoundException,
    PurchaseNotPendingException,
)
from app.purchases.models import Purchase
from app.purchases.services import PurchaseService

# ──────────────────────────────────────────────────────────────────────────────
# Fixtures
# ──────────────────────────────────────────────────────────────────────────────


@pytest.fixture
def purchase_service_mock() -> Mock:
    return create_autospec(PurchaseService)


@pytest.fixture
def uow_mock() -> Mock:
    mock = Mock(spec=UnitOfWorkABC)
    mock.commit = AsyncMock()
    return mock


async def _mock_get_async_db() -> AsyncGenerator[AsyncMock, Any]:
    yield AsyncMock()


@pytest.fixture
def client(
    purchase_service_mock: Mock, uow_mock: Mock
) -> Generator[TestClient, None, None]:
    app.dependency_overrides[get_async_db] = _mock_get_async_db
    app.dependency_overrides[get_purchase_service] = lambda: purchase_service_mock
    app.dependency_overrides[get_unit_of_work] = lambda: uow_mock
    app.dependency_overrides[get_current_admin_user] = lambda: Mock()

    test_client = TestClient(app)
    yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def non_admin_client(
    purchase_service_mock: Mock,
    uow_mock: Mock,
) -> Generator[TestClient, None, None]:
    def _raise_invalid_token() -> None:
        raise InvalidTokenException()

    app.dependency_overrides[get_async_db] = _mock_get_async_db
    app.dependency_overrides[get_purchase_service] = lambda: purchase_service_mock
    app.dependency_overrides[get_unit_of_work] = lambda: uow_mock
    app.dependency_overrides[get_current_admin_user] = _raise_invalid_token

    yield TestClient(app)

    app.dependency_overrides.clear()


@pytest.fixture
def unauthenticated_client(
    purchase_service_mock: Mock,
    uow_mock: Mock,
) -> Generator[TestClient, None, None]:
    """Client that does NOT override the auth dependency — auth is absent."""
    app.dependency_overrides[get_async_db] = _mock_get_async_db
    app.dependency_overrides[get_purchase_service] = lambda: purchase_service_mock
    app.dependency_overrides[get_unit_of_work] = lambda: uow_mock

    yield TestClient(app, raise_server_exceptions=False)

    app.dependency_overrides.clear()


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────


def _assert_paginated_response(
    data: dict[str, Any],
    expected_total: int,
    expected_offset: int,
    expected_limit: int,
) -> None:
    assert data["pagination"]["total"] == expected_total
    assert data["pagination"]["offset"] == expected_offset
    assert data["pagination"]["limit"] == expected_limit
    assert "data" in data
    assert isinstance(data["data"], list)


def _assert_error_payload(data: dict[str, Any], expected_code: str) -> None:
    assert "error" in data
    assert data["error"]["code"] == expected_code


def _assert_purchase_item_response(item: dict[str, Any], purchase: Purchase) -> None:
    assert item["id"] == purchase.id
    assert item["external_id"] == purchase.external_id
    assert item["user_id"] == purchase.user_id
    assert item["merchant_id"] == purchase.merchant_id
    assert item["offer_id"] == purchase.offer_id
    assert Decimal(item["amount"]) == purchase.amount
    assert item["currency"] == purchase.currency
    assert item["status"] == purchase.status


# ──────────────────────────────────────────────────────────────────────────────
# GET /api/v1/purchases — success
# ──────────────────────────────────────────────────────────────────────────────


def test_list_all_purchases_returns_200_on_success(
    client: TestClient,
    purchase_service_mock: Mock,
    purchase_factory: Callable[..., Purchase],
) -> None:
    # Arrange
    purchase = purchase_factory()
    purchase_service_mock.list_purchases.return_value = ([purchase], 1)

    # Act
    response = client.get("/api/v1/purchases")

    # Assert
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    _assert_paginated_response(
        data, expected_total=1, expected_offset=0, expected_limit=10
    )
    assert len(data["data"]) == 1
    assert data["data"][0]["id"] == purchase.id


def test_list_all_purchases_returns_empty_list_when_no_results(
    client: TestClient,
    purchase_service_mock: Mock,
) -> None:
    # Arrange
    purchase_service_mock.list_purchases.return_value = ([], 0)

    # Act
    response = client.get("/api/v1/purchases")

    # Assert
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    _assert_paginated_response(
        data, expected_total=0, expected_offset=0, expected_limit=10
    )
    assert data["data"] == []


def test_list_all_purchases_returns_correct_item_fields(
    client: TestClient,
    purchase_service_mock: Mock,
    purchase_factory: Callable[..., Purchase],
) -> None:
    # Arrange
    purchase = purchase_factory()
    purchase_service_mock.list_purchases.return_value = ([purchase], 1)

    # Act
    response = client.get("/api/v1/purchases")

    # Assert
    assert response.status_code == status.HTTP_200_OK
    item = response.json()["data"][0]
    _assert_purchase_item_response(item, purchase)


def test_list_all_purchases_reflects_pagination_params(
    client: TestClient,
    purchase_service_mock: Mock,
) -> None:
    # Arrange
    purchase_service_mock.list_purchases.return_value = ([], 0)
    requested_offset = 10
    requested_limit = 5

    # Act
    response = client.get(
        f"/api/v1/purchases?offset={requested_offset}&limit={requested_limit}"
    )

    # Assert
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["pagination"]["offset"] == requested_offset
    assert data["pagination"]["limit"] == requested_limit


def test_list_all_purchases_passes_filters_to_service(
    client: TestClient,
    purchase_service_mock: Mock,
) -> None:
    # Arrange
    purchase_service_mock.list_purchases.return_value = ([], 0)
    user_id = "b7e2c1a2-4f3a-4e2b-9c1a-8d2e3f4b5c6d"
    merchant_id = "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d"

    # Act
    client.get(
        f"/api/v1/purchases?status=confirmed&user_id={user_id}"
        f"&merchant_id={merchant_id}&start_date=2026-01-01&end_date=2026-03-31"
    )

    # Assert
    purchase_service_mock.list_purchases.assert_called_once()
    call_kwargs = purchase_service_mock.list_purchases.call_args.kwargs
    assert call_kwargs["status"] == "confirmed"
    assert call_kwargs["user_id"] == user_id
    assert call_kwargs["merchant_id"] == merchant_id
    assert str(call_kwargs["start_date"]) == "2026-01-01"
    assert str(call_kwargs["end_date"]) == "2026-03-31"


# ──────────────────────────────────────────────────────────────────────────────
# GET /api/v1/purchases — exception handling
# ──────────────────────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "side_effect,expected_status,expected_code",
    [
        (
            InvalidPurchaseStatusException("invalid_status"),
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            PurchaseErrorCode.INVALID_PURCHASE_STATUS,
        ),
        (
            Exception("unexpected failure"),
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            ErrorCode.INTERNAL_SERVER_ERROR,
        ),
    ],
)
def test_list_all_purchases_returns_error_on_exception(
    client: TestClient,
    purchase_service_mock: Mock,
    side_effect: Exception,
    expected_status: int,
    expected_code: str,
) -> None:
    # Arrange
    purchase_service_mock.list_purchases.side_effect = side_effect

    # Act
    response = client.get("/api/v1/purchases")

    # Assert
    assert response.status_code == expected_status
    _assert_error_payload(response.json(), expected_code)


# ──────────────────────────────────────────────────────────────────────────────
# GET /api/v1/purchases — authorization
# ──────────────────────────────────────────────────────────────────────────────


def test_list_all_purchases_returns_401_on_missing_auth(
    unauthenticated_client: TestClient,
) -> None:
    # Act
    response = unauthenticated_client.get("/api/v1/purchases")

    # Assert
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_list_all_purchases_returns_401_on_non_admin(
    non_admin_client: TestClient,
) -> None:
    # Act
    response = non_admin_client.get("/api/v1/purchases")

    # Assert
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    _assert_error_payload(response.json(), ErrorCode.INVALID_TOKEN)


# ──────────────────────────────────────────────────────────────────────────────
# GET /api/v1/purchases — pagination validation
# ──────────────────────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "query_string,description",
    [
        ("offset=-1", "offset below minimum"),
        ("limit=0", "limit below minimum"),
        ("limit=101", "limit above maximum"),
    ],
)
def test_list_all_purchases_returns_422_on_invalid_pagination_params(
    client: TestClient,
    query_string: str,
    description: str,
) -> None:
    # Act
    response = client.get(f"/api/v1/purchases?{query_string}")

    # Assert
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT, (
        f"Expected 422 for: {description}"
    )


# ──────────────────────────────────────────────────────────────────────────────
# PATCH /api/v1/purchases/{purchase_id}/reverse — success
# ──────────────────────────────────────────────────────────────────────────────


def test_reverse_purchase_returns_200_on_success(
    client: TestClient,
    purchase_service_mock: Mock,
    purchase_factory: Callable[..., Purchase],
) -> None:
    # Arrange
    purchase = purchase_factory(status="reversed", cashback_amount=Decimal("0"))
    purchase_service_mock.reverse_purchase = AsyncMock(return_value=purchase)

    # Act
    response = client.patch(f"/api/v1/purchases/{purchase.id}/reverse")

    # Assert
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == purchase.id
    assert data["status"] == "reversed"
    assert Decimal(data["cashback_amount"]) == Decimal("0")


def test_reverse_purchase_calls_service_with_correct_args(
    client: TestClient,
    purchase_service_mock: Mock,
    purchase_factory: Callable[..., Purchase],
) -> None:
    # Arrange
    purchase = purchase_factory(status="reversed", cashback_amount=Decimal("0"))
    purchase_service_mock.reverse_purchase = AsyncMock(return_value=purchase)
    purchase_id = purchase.id

    # Act
    client.patch(f"/api/v1/purchases/{purchase_id}/reverse")

    # Assert
    purchase_service_mock.reverse_purchase.assert_called_once()
    call_args = purchase_service_mock.reverse_purchase.call_args
    assert call_args.args[0] == purchase_id


# ──────────────────────────────────────────────────────────────────────────────
# PATCH /api/v1/purchases/{purchase_id}/reverse — exception handling
# ──────────────────────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "side_effect,expected_status,expected_code",
    [
        (
            PurchaseNotFoundException("some-purchase-id"),
            status.HTTP_404_NOT_FOUND,
            ErrorCode.NOT_FOUND,
        ),
        (
            PurchaseAlreadyReversedException("some-purchase-id"),
            status.HTTP_400_BAD_REQUEST,
            PurchaseErrorCode.PURCHASE_ALREADY_REVERSED,
        ),
        (
            Exception("unexpected failure"),
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            ErrorCode.INTERNAL_SERVER_ERROR,
        ),
    ],
)
def test_reverse_purchase_returns_error_on_exception(
    client: TestClient,
    purchase_service_mock: Mock,
    side_effect: Exception,
    expected_status: int,
    expected_code: str,
) -> None:
    # Arrange
    purchase_id = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
    purchase_service_mock.reverse_purchase = AsyncMock(side_effect=side_effect)

    # Act
    response = client.patch(f"/api/v1/purchases/{purchase_id}/reverse")

    # Assert
    assert response.status_code == expected_status
    _assert_error_payload(response.json(), expected_code)


def test_reverse_purchase_returns_already_reversed_details(
    client: TestClient,
    purchase_service_mock: Mock,
) -> None:
    # Arrange
    purchase_id = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
    exc = PurchaseAlreadyReversedException(purchase_id)
    purchase_service_mock.reverse_purchase = AsyncMock(side_effect=exc)

    # Act
    response = client.patch(f"/api/v1/purchases/{purchase_id}/reverse")

    # Assert
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data = response.json()
    violation = data["error"]["details"]["violations"][0]
    assert violation["purchase_id"] == purchase_id
    assert violation["current_status"] == "reversed"
    assert "pending" in violation["reversible_from_statuses"]
    assert "confirmed" in violation["reversible_from_statuses"]


# ──────────────────────────────────────────────────────────────────────────────
# PATCH /api/v1/purchases/{purchase_id}/reverse — authorization
# ──────────────────────────────────────────────────────────────────────────────


def test_reverse_purchase_returns_401_on_missing_auth(
    unauthenticated_client: TestClient,
) -> None:
    # Act
    response = unauthenticated_client.patch(
        "/api/v1/purchases/aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee/reverse"
    )

    # Assert
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_reverse_purchase_returns_401_on_non_admin(
    non_admin_client: TestClient,
) -> None:
    # Act
    response = non_admin_client.patch(
        "/api/v1/purchases/aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee/reverse"
    )

    # Assert
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    _assert_error_payload(response.json(), ErrorCode.INVALID_TOKEN)


# ──────────────────────────────────────────────────────────────────────────────
# POST /api/v1/purchases/{purchase_id}/confirmation — success
# ──────────────────────────────────────────────────────────────────────────────


def test_admin_confirm_purchase_returns_200_on_success(
    client: TestClient,
    purchase_service_mock: Mock,
    purchase_factory: Callable[..., Purchase],
) -> None:
    # Arrange
    purchase = purchase_factory(status="confirmed", cashback_amount=Decimal("10.00"))
    purchase_service_mock.confirm_purchase_manually = AsyncMock(return_value=purchase)

    # Act
    response = client.post(f"/api/v1/purchases/{purchase.id}/confirmation")

    # Assert
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == purchase.id
    assert data["status"] == "confirmed"
    assert Decimal(data["cashback_amount"]) == Decimal("10.00")


def test_admin_confirm_purchase_calls_service_with_correct_args(
    client: TestClient,
    purchase_service_mock: Mock,
    purchase_factory: Callable[..., Purchase],
) -> None:
    # Arrange
    purchase = purchase_factory(status="confirmed", cashback_amount=Decimal("10.00"))
    purchase_service_mock.confirm_purchase_manually = AsyncMock(return_value=purchase)
    purchase_id = purchase.id
    admin_user = Mock()
    admin_user.id = "aaaaaaaa-bbbb-cccc-dddd-000000000001"

    # Override the current_admin_user dependency to return a known admin
    app.dependency_overrides[get_current_admin_user] = lambda: admin_user

    # Act
    client.post(f"/api/v1/purchases/{purchase_id}/confirmation")

    # Assert
    purchase_service_mock.confirm_purchase_manually.assert_called_once()
    call_args = purchase_service_mock.confirm_purchase_manually.call_args
    assert call_args.args[0] == purchase_id
    assert call_args.args[1] == "aaaaaaaa-bbbb-cccc-dddd-000000000001"

    # Clean up
    app.dependency_overrides.pop(get_current_admin_user, None)


# ──────────────────────────────────────────────────────────────────────────────
# POST /api/v1/purchases/{purchase_id}/confirmation — exception handling
# ──────────────────────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "side_effect,expected_status,expected_code",
    [
        (
            PurchaseNotFoundException("some-purchase-id"),
            status.HTTP_404_NOT_FOUND,
            ErrorCode.NOT_FOUND,
        ),
        (
            PurchaseNotPendingException("some-purchase-id", "confirmed"),
            status.HTTP_400_BAD_REQUEST,
            PurchaseErrorCode.PURCHASE_NOT_PENDING,
        ),
        (
            Exception("unexpected failure"),
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            ErrorCode.INTERNAL_SERVER_ERROR,
        ),
    ],
)
def test_admin_confirm_purchase_returns_error_on_exception(
    client: TestClient,
    purchase_service_mock: Mock,
    side_effect: Exception,
    expected_status: int,
    expected_code: str,
) -> None:
    # Arrange
    purchase_id = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
    purchase_service_mock.confirm_purchase_manually = AsyncMock(side_effect=side_effect)

    # Act
    response = client.post(f"/api/v1/purchases/{purchase_id}/confirmation")

    # Assert
    assert response.status_code == expected_status
    _assert_error_payload(response.json(), expected_code)


def test_admin_confirm_purchase_returns_not_pending_details(
    client: TestClient,
    purchase_service_mock: Mock,
) -> None:
    # Arrange
    purchase_id = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
    exc = PurchaseNotPendingException(purchase_id, "confirmed")
    purchase_service_mock.confirm_purchase_manually = AsyncMock(side_effect=exc)

    # Act
    response = client.post(f"/api/v1/purchases/{purchase_id}/confirmation")

    # Assert
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data = response.json()
    violation = data["error"]["details"]["violations"][0]
    assert violation["purchase_id"] == purchase_id
    assert violation["current_status"] == "confirmed"
    assert violation["required_status"] == "pending"


# ──────────────────────────────────────────────────────────────────────────────
# POST /api/v1/purchases/{purchase_id}/confirmation — authorization
# ──────────────────────────────────────────────────────────────────────────────


def test_admin_confirm_purchase_returns_401_on_missing_auth(
    unauthenticated_client: TestClient,
) -> None:
    # Act
    response = unauthenticated_client.post(
        "/api/v1/purchases/aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee/confirmation"
    )

    # Assert
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_admin_confirm_purchase_returns_401_on_non_admin(
    non_admin_client: TestClient,
) -> None:
    # Act
    response = non_admin_client.post(
        "/api/v1/purchases/aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee/confirmation"
    )

    # Assert
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    _assert_error_payload(response.json(), ErrorCode.INVALID_TOKEN)
