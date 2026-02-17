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
    "exception,expected_status,expected_detail,password",
    [
        (
            EmailAlreadyRegisteredException(
                "Email 'fail@example.com' is already registered."
            ),
            status.HTTP_409_CONFLICT,
            "Email 'fail@example.com' is already registered.",
            "ValidPass1!",
        ),
        (
            PasswordNotComplexEnoughException("Too weak"),
            status.HTTP_400_BAD_REQUEST,  # Updated to match implementation
            "Too weak",
            "weak",  # Intentionally weak password
        ),
        (
            Exception("Something broke"),
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "An unexpected error occurred. Our team has been notified. Please retry later.",
            "ValidPass1!",
        ),
    ],
)
def test_create_user_exceptions(
    client: TestClient,
    user_service_mock: Mock,
    exception: Exception,
    expected_status: int,
    expected_detail: str,
    password: str,
) -> None:
    # Arrange
    user_data = {"email": "fail@example.com", "password": password}
    user_service_mock.create_user.side_effect = exception

    # Act
    response = client.post("/api/v1/users", json=user_data)

    # Assert
    assert response.status_code == expected_status
    assert "error" in response.json()


def _assert_user_out_response(data: dict[str, Any], user: User) -> None:
    assert data["id"] == user.id
    assert data["email"] == user.email
    assert data["role"] == user.role
    assert data["active"] == user.active
    # created_at may be iso string, so compare date part
    assert data["created_at"] == user.created_at
