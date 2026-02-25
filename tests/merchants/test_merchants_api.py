from typing import Any, Callable, Generator
from unittest.mock import Mock, create_autospec

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.core.current_user import get_current_admin_user
from app.core.database import get_db
from app.core.errors.codes import ErrorCode
from app.main import app
from app.merchants.composition import get_merchant_service
from app.merchants.exceptions import CashbackPercentageNotValidException
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


def test_create_merchant_success(
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
def test_create_merchant_exceptions(
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


def test_create_merchant_cashback_error_details(
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
