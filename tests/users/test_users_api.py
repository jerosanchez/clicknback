from typing import Any, Generator
from unittest.mock import Mock, create_autospec

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.core.database import get_db
from app.main import app
from app.users.api import get_user_service
from app.users.exceptions import (
    EmailAlreadyRegisteredException,
    PasswordNotComplexEnoughException,
)
from app.users.models import User
from app.users.services import UserService


@pytest.fixture
def user_service_mock():
    return create_autospec(UserService)


@pytest.fixture
def client(user_service_mock: Mock) -> Generator[TestClient, None, None]:
    def mock_get_db():
        yield Mock()

    app.dependency_overrides[get_db] = mock_get_db
    app.dependency_overrides[get_user_service] = lambda: user_service_mock

    client = TestClient(app)
    yield client

    app.dependency_overrides.clear()


def test_create_user_success(
    client: TestClient, user_service_mock: Mock, user_factory: Any
) -> None:
    # Arrange
    user_data = {"email": "test@example.com", "password": "ValidPass1!"}
    user = user_factory()
    user_service_mock.create_user.return_value = user

    # Act
    response = client.post("/api/v1/users", json=user_data)

    # Assert
    assert response.status_code == status.HTTP_201_CREATED
    _assert_user_out_response(response.json(), user)


@pytest.mark.parametrize(
    "exception,expected_status",
    [
        (
            PasswordNotComplexEnoughException("Some reason."),
            status.HTTP_400_BAD_REQUEST,
        ),
        (
            EmailAlreadyRegisteredException("existing@example.com"),
            status.HTTP_409_CONFLICT,
        ),
        (
            Exception("Something broke"),
            status.HTTP_500_INTERNAL_SERVER_ERROR,
        ),
    ],
)
def test_create_user_exceptions(
    client: TestClient,
    user_service_mock: Mock,
    exception: Exception,
    expected_status: int,
) -> None:
    # Arrange
    request_data = {"email": "fail@example.com", "password": "anything"}
    user_service_mock.create_user.side_effect = exception

    # Act
    response = client.post("/api/v1/users", json=request_data)

    # Assert
    assert response.status_code == expected_status
    response_data = response.json()

    _assert_error_payload(exception, response_data)


def _assert_user_out_response(data: dict[str, Any], user: User) -> None:
    assert data["id"] == user.id
    assert data["email"] == user.email
    assert data["role"] == user.role
    assert data["active"] == user.active
    assert data["created_at"] == user.created_at


def _assert_error_payload(exception: Exception, data: dict[str, Any]) -> None:
    if isinstance(exception, EmailAlreadyRegisteredException):
        _assert_email_already_registered_error(exception, data)

    elif isinstance(exception, PasswordNotComplexEnoughException):
        _assert_password_not_complex_enough_error(exception, data)

    else:
        # For generic exceptions, expect a generic code
        assert "error" in data
        error = data["error"]
        assert error.get("code") == "INTERNAL_SERVER_ERROR"


def _assert_email_already_registered_error(
    exception: EmailAlreadyRegisteredException, data: dict[str, Any]
) -> None:
    assert "error" in data
    error = data["error"]
    assert error.get("code") == "EMAIL_ALREADY_REGISTERED"
    assert "details" in error
    assert "email" in error["details"]
    assert error["details"]["email"] == exception.email


def _assert_password_not_complex_enough_error(
    exception: PasswordNotComplexEnoughException, data: dict[str, Any]
) -> None:
    assert "error" in data
    error = data["error"]
    assert error.get("code") == "PASSWORD_NOT_COMPLEX_ENOUGH"
    assert "details" in error
    assert "violations" in error["details"]

    violation_entry: dict[str, Any] = {
        "field": "password",
        "reason": exception.reason,
    }
    assert violation_entry in error["details"]["violations"]
