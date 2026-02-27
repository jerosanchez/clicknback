from typing import Any, Callable, Generator
from unittest.mock import Mock, create_autospec

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.core.database import get_db
from app.core.errors.codes import ErrorCode as CoreErrorCode
from app.main import app
from app.users.api import get_user_service
from app.users.errors import ErrorCode as UserErrorCode
from app.users.exceptions import (
    EmailAlreadyRegisteredException,
    PasswordNotComplexEnoughException,
)
from app.users.models import User
from app.users.services import UserService


@pytest.fixture
def user_service_mock() -> Mock:
    return create_autospec(UserService)


@pytest.fixture
def client(user_service_mock: Mock) -> Generator[TestClient, None, None]:
    def mock_get_db() -> Generator[Mock, None, None]:
        yield Mock()

    app.dependency_overrides[get_db] = mock_get_db
    app.dependency_overrides[get_user_service] = lambda: user_service_mock

    test_client = TestClient(app)
    yield test_client

    app.dependency_overrides.clear()


def _assert_user_out_response(data: dict[str, Any], user: User) -> None:
    assert data["id"] == str(user.id)
    assert data["email"] == user.email
    assert data["role"] == user.role
    assert data["active"] == user.active


def _assert_error_payload(data: dict[str, Any], expected_code: str) -> None:
    assert "error" in data
    assert data["error"]["code"] == expected_code


def _assert_email_already_registered_error_response(
    data: dict[str, Any], exc: EmailAlreadyRegisteredException
) -> None:
    assert data["error"]["code"] == UserErrorCode.EMAIL_ALREADY_REGISTERED
    assert data["error"]["details"]["email"] == exc.email


def _assert_password_not_complex_enough_error_response(
    data: dict[str, Any], exc: PasswordNotComplexEnoughException
) -> None:
    assert data["error"]["code"] == UserErrorCode.PASSWORD_NOT_COMPLEX_ENOUGH
    assert {"field": "password", "reason": exc.reason} in data["error"]["details"][
        "violations"
    ]


# ──────────────────────────────────────────────────────────────────────────────
# POST /api/v1/users
# ──────────────────────────────────────────────────────────────────────────────


def test_create_user_returns_201_on_success(
    client: TestClient,
    user_service_mock: Mock,
    user_factory: Callable[..., User],
    user_input_data: Callable[[User], dict[str, Any]],
) -> None:
    # Arrange
    user = user_factory()
    user_service_mock.create_user.return_value = user
    request_data = user_input_data(user)

    # Act
    response = client.post("/api/v1/users", json=request_data)

    # Assert
    assert response.status_code == status.HTTP_201_CREATED
    _assert_user_out_response(response.json(), user)


@pytest.mark.parametrize(
    "exception,expected_status,expected_code",
    [
        (
            PasswordNotComplexEnoughException("Some reason."),
            status.HTTP_400_BAD_REQUEST,
            UserErrorCode.PASSWORD_NOT_COMPLEX_ENOUGH,
        ),
        (
            EmailAlreadyRegisteredException("existing@example.com"),
            status.HTTP_409_CONFLICT,
            UserErrorCode.EMAIL_ALREADY_REGISTERED,
        ),
        (
            Exception("Something broke"),
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            CoreErrorCode.INTERNAL_SERVER_ERROR,
        ),
    ],
)
def test_create_user_returns_error_on_exception(
    client: TestClient,
    user_service_mock: Mock,
    user_factory: Callable[..., User],
    user_input_data: Callable[[User], dict[str, Any]],
    exception: Exception,
    expected_status: int,
    expected_code: str,
) -> None:
    # Arrange
    request_data = user_input_data(user_factory())
    user_service_mock.create_user.side_effect = exception

    # Act
    response = client.post("/api/v1/users", json=request_data)

    # Assert
    assert response.status_code == expected_status
    _assert_error_payload(response.json(), expected_code)


def test_create_user_returns_409_with_details_on_email_already_registered(
    client: TestClient,
    user_service_mock: Mock,
    user_factory: Callable[..., User],
    user_input_data: Callable[[User], dict[str, Any]],
) -> None:
    # Arrange
    exc = EmailAlreadyRegisteredException("existing@example.com")
    user_service_mock.create_user.side_effect = exc
    request_data = user_input_data(user_factory())

    # Act
    response = client.post("/api/v1/users", json=request_data)

    # Assert
    assert response.status_code == status.HTTP_409_CONFLICT
    _assert_email_already_registered_error_response(response.json(), exc)


def test_create_user_returns_400_with_details_on_password_not_complex_enough(
    client: TestClient,
    user_service_mock: Mock,
    user_factory: Callable[..., User],
    user_input_data: Callable[[User], dict[str, Any]],
) -> None:
    # Arrange
    exc = PasswordNotComplexEnoughException("Some reason.")
    user_service_mock.create_user.side_effect = exc
    request_data = user_input_data(user_factory())

    # Act
    response = client.post("/api/v1/users", json=request_data)

    # Assert
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    _assert_password_not_complex_enough_error_response(response.json(), exc)
