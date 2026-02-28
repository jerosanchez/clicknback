from typing import Any, Callable, Generator
from unittest.mock import Mock, create_autospec

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.core.config import settings
from app.core.current_user import get_current_admin_user
from app.core.database import get_db
from app.core.errors.builders import forbidden_error
from app.core.errors.codes import ErrorCode
from app.main import app
from app.merchants.composition import get_merchant_service
from app.merchants.exceptions import (
    CashbackPercentageNotValidException,
    MerchantNotFoundException,
)
from app.merchants.models import Merchant
from app.merchants.services import MerchantService


@pytest.fixture
def merchant_service_mock() -> Mock:
    return create_autospec(MerchantService)


@pytest.fixture
def client(merchant_service_mock: Mock) -> Generator[TestClient, None, None]:
    def mock_get_db():
        yield Mock()

    app.dependency_overrides[get_db] = mock_get_db
    app.dependency_overrides[get_merchant_service] = lambda: merchant_service_mock
    app.dependency_overrides[get_current_admin_user] = lambda: Mock()

    test_client = TestClient(app)
    yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def non_admin_client(
    merchant_service_mock: Mock,
) -> Generator[TestClient, None, None]:
    def mock_get_db() -> Generator[Mock, None, None]:
        yield Mock()

    def raise_forbidden() -> None:
        raise forbidden_error("Admin access required.", {})

    app.dependency_overrides[get_db] = mock_get_db
    app.dependency_overrides[get_merchant_service] = lambda: merchant_service_mock
    app.dependency_overrides[get_current_admin_user] = raise_forbidden

    yield TestClient(app)

    app.dependency_overrides.clear()


def _assert_merchant_out_response(data: dict[str, Any], merchant: Merchant) -> None:
    assert data["id"] == str(merchant.id)
    assert data["name"] == merchant.name
    assert data["default_cashback_percentage"] == merchant.default_cashback_percentage
    assert data["active"] == merchant.active


def _assert_error_payload(data: dict[str, Any], expected_code: ErrorCode) -> None:
    assert "error" in data
    assert data["error"]["code"] == expected_code


def _assert_cashback_percentage_error_response(
    data: dict[str, Any], exc: CashbackPercentageNotValidException
) -> None:
    assert data["error"]["code"] == ErrorCode.VALIDATION_ERROR
    assert data["error"]["details"]["field"] == "default_cashback_percentage"
    assert data["error"]["details"]["reason"] == str(exc)


# ──────────────────────────────────────────────────────────────────────────────
# POST /api/v1/merchants
# ──────────────────────────────────────────────────────────────────────────────


def test_create_merchant_returns_201_on_success(
    client: TestClient,
    merchant_service_mock: Mock,
    merchant_factory: Callable[..., Merchant],
    merchant_input_data: Callable[[Merchant], dict[str, Any]],
) -> None:
    # Arrange
    merchant = merchant_factory()
    merchant_service_mock.create_merchant.return_value = merchant
    request_data = merchant_input_data(merchant)

    # Act
    response = client.post("/api/v1/merchants", json=request_data)

    # Assert
    assert response.status_code == status.HTTP_201_CREATED
    _assert_merchant_out_response(response.json(), merchant)


@pytest.mark.parametrize(
    "exception,expected_status,expected_code",
    [
        (
            CashbackPercentageNotValidException("Must be between 0 and 20."),
            status.HTTP_409_CONFLICT,
            ErrorCode.VALIDATION_ERROR,
        ),
        (
            Exception("Something broke"),
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            ErrorCode.INTERNAL_SERVER_ERROR,
        ),
    ],
)
def test_create_merchant_returns_error_on_exception(
    client: TestClient,
    merchant_service_mock: Mock,
    merchant_factory: Callable[..., Merchant],
    merchant_input_data: Callable[[Merchant], dict[str, Any]],
    exception: Exception,
    expected_status: int,
    expected_code: ErrorCode,
) -> None:
    # Arrange
    request_data = merchant_input_data(merchant_factory())
    merchant_service_mock.create_merchant.side_effect = exception

    # Act
    response = client.post("/api/v1/merchants", json=request_data)

    # Assert
    assert response.status_code == expected_status
    _assert_error_payload(response.json(), expected_code)


def test_create_merchant_returns_403_on_non_admin(
    non_admin_client: TestClient,
    merchant_factory: Callable[..., Merchant],
    merchant_input_data: Callable[[Merchant], dict[str, Any]],
) -> None:
    # Act
    response = non_admin_client.post(
        "/api/v1/merchants", json=merchant_input_data(merchant_factory())
    )

    # Assert
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_create_merchant_returns_409_with_details_on_invalid_cashback(
    client: TestClient,
    merchant_service_mock: Mock,
    merchant_factory: Callable[..., Merchant],
    merchant_input_data: Callable[[Merchant], dict[str, Any]],
) -> None:
    # Arrange
    invalid_reason = "Must be between 0 and 20."
    exc = CashbackPercentageNotValidException(invalid_reason)
    merchant_service_mock.create_merchant.side_effect = exc
    request_data = merchant_input_data(merchant_factory())

    # Act
    response = client.post("/api/v1/merchants", json=request_data)

    # Assert
    assert response.status_code == status.HTTP_409_CONFLICT
    _assert_cashback_percentage_error_response(response.json(), exc)


# ──────────────────────────────────────────────────────────────────────────────
# GET /merchants
# ──────────────────────────────────────────────────────────────────────────────


def test_list_merchants_returns_200_on_success(
    client: TestClient,
    merchant_service_mock: Mock,
    merchant_factory: Callable[..., Merchant],
) -> None:
    # Arrange
    uuids = [
        "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
        "b2c3d4e5-f6a7-8901-bcde-f12345678901",
        "c3d4e5f6-a7b8-9012-cdef-123456789012",
    ]
    merchants = [merchant_factory(id=uuids[i], name=f"Shop {i}") for i in range(3)]
    merchant_service_mock.list_merchants.return_value = (merchants, 3)

    # Act
    response = client.get("/api/v1/merchants")

    # Assert
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["total"] == 3
    assert data["page"] == 1
    assert data["page_size"] == 20
    assert len(data["items"]) == 3


def test_list_merchants_returns_200_on_empty_results(
    client: TestClient,
    merchant_service_mock: Mock,
) -> None:
    # Arrange
    merchant_service_mock.list_merchants.return_value = ([], 0)

    # Act
    response = client.get("/api/v1/merchants")

    # Assert
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["total"] == 0
    assert data["items"] == []


@pytest.mark.parametrize(
    "exception,expected_status,expected_code",
    [
        (
            Exception("Something broke"),
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            ErrorCode.INTERNAL_SERVER_ERROR,
        ),
    ],
)
def test_list_merchants_returns_error_on_exception(
    client: TestClient,
    merchant_service_mock: Mock,
    exception: Exception,
    expected_status: int,
    expected_code: ErrorCode,
) -> None:
    # Arrange
    merchant_service_mock.list_merchants.side_effect = exception

    # Act
    response = client.get("/api/v1/merchants")

    # Assert
    assert response.status_code == expected_status
    _assert_error_payload(response.json(), expected_code)


def test_list_merchants_returns_403_on_non_admin(
    non_admin_client: TestClient,
) -> None:
    # Act
    response = non_admin_client.get("/api/v1/merchants")

    # Assert
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.parametrize(
    "query_string",
    [
        "page=0",  # below minimum page
        "page_size=0",  # below minimum page_size
        f"page_size={settings.max_page_size + 1}",  # above maximum page_size
    ],
)
def test_list_merchants_returns_422_on_invalid_pagination_params(
    client: TestClient,
    query_string: str,
) -> None:
    # Act
    response = client.get(f"/api/v1/merchants?{query_string}")

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
def test_list_merchants_returns_200_on_valid_pagination_params(
    client: TestClient,
    merchant_service_mock: Mock,
    query_string: str,
) -> None:
    # Arrange
    merchant_service_mock.list_merchants.return_value = ([], 0)

    # Act
    response = client.get(f"/api/v1/merchants?{query_string}")

    # Assert
    assert response.status_code == status.HTTP_200_OK


# ──────────────────────────────────────────────────────────────────────────────
# PATCH /api/v1/merchants/{merchant_id}/status
# ──────────────────────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "target_status,expected_active",
    [
        ("active", True),
        ("inactive", False),
    ],
)
def test_set_merchant_status_returns_200_with_updated_status(
    client: TestClient,
    merchant_service_mock: Mock,
    merchant_factory: Callable[..., Merchant],
    target_status: str,
    expected_active: bool,
) -> None:
    # Arrange
    merchant = merchant_factory(active=expected_active)
    merchant_service_mock.set_merchant_status.return_value = merchant

    # Act
    response = client.patch(
        f"/api/v1/merchants/{merchant.id}/status",
        json={"status": target_status},
    )

    # Assert
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == str(merchant.id)
    assert data["status"] == target_status


def test_set_merchant_status_returns_404_when_merchant_not_found(
    client: TestClient,
    merchant_service_mock: Mock,
) -> None:
    # Arrange
    not_found_merchant_id = "00000000-0000-0000-0000-000000000000"
    merchant_service_mock.set_merchant_status.side_effect = MerchantNotFoundException(
        not_found_merchant_id
    )

    # Act
    response = client.patch(
        f"/api/v1/merchants/{not_found_merchant_id}/status",
        json={"status": "active"},
    )

    # Assert
    assert response.status_code == status.HTTP_404_NOT_FOUND
    _assert_error_payload(response.json(), ErrorCode.NOT_FOUND)


def test_set_merchant_status_returns_403_on_non_admin(
    non_admin_client: TestClient,
    merchant_factory: Callable[..., Merchant],
) -> None:
    # Arrange
    merchant = merchant_factory()

    # Act
    response = non_admin_client.patch(
        f"/api/v1/merchants/{merchant.id}/status",
        json={"status": "active"},
    )

    # Assert
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_set_merchant_status_returns_422_on_invalid_status_value(
    client: TestClient,
    merchant_factory: Callable[..., Merchant],
) -> None:
    # Arrange
    merchant = merchant_factory()

    # Act
    response = client.patch(
        f"/api/v1/merchants/{merchant.id}/status",
        json={"status": "unknown_status"},
    )

    # Assert
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


def test_set_merchant_status_returns_500_on_unexpected_error(
    client: TestClient,
    merchant_service_mock: Mock,
    merchant_factory: Callable[..., Merchant],
) -> None:
    # Arrange
    merchant = merchant_factory()
    merchant_service_mock.set_merchant_status.side_effect = Exception("Something broke")

    # Act
    response = client.patch(
        f"/api/v1/merchants/{merchant.id}/status",
        json={"status": "active"},
    )

    # Assert
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    _assert_error_payload(response.json(), ErrorCode.INTERNAL_SERVER_ERROR)
