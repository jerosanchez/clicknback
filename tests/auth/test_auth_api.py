from typing import Any, Generator
from unittest.mock import Mock, create_autospec

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.auth.composition import get_auth_service
from app.auth.exceptions import PasswordVerificationException, UserNotFoundException
from app.auth.models import Token
from app.auth.services import AuthService
from app.core.database import get_db
from app.main import app


@pytest.fixture
def auth_service_mock() -> Mock:
    return create_autospec(AuthService)


@pytest.fixture
def client(auth_service_mock: Mock) -> Generator[TestClient, None, None]:
    def mock_get_db() -> Generator[Mock, None, None]:
        yield Mock()

    app.dependency_overrides[get_db] = mock_get_db
    app.dependency_overrides[get_auth_service] = lambda: auth_service_mock

    test_client = TestClient(app)
    yield test_client

    app.dependency_overrides.clear()


def test_login_success(client: TestClient, auth_service_mock: Mock) -> None:
    # Arrange
    login_data = {"email": "alice@example.com", "password": "ValidPass1!"}
    token = Token(access_token="some.jwt.token", token_type="bearer")
    auth_service_mock.login.return_value = token

    # Act
    response = client.post("/api/v1/login", json=login_data)

    # Assert
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["access_token"] == token.access_token
    assert data["token_type"] == token.token_type


@pytest.mark.parametrize(
    "exception,expected_status",
    [
        (
            UserNotFoundException("alice@example.com"),
            status.HTTP_401_UNAUTHORIZED,
        ),
        (
            PasswordVerificationException(),
            status.HTTP_401_UNAUTHORIZED,
        ),
        (
            Exception("Something broke"),
            status.HTTP_500_INTERNAL_SERVER_ERROR,
        ),
    ],
)
def test_login_exceptions(
    client: TestClient,
    auth_service_mock: Mock,
    exception: Exception,
    expected_status: int,
) -> None:
    # Arrange
    login_data = {"email": "alice@example.com", "password": "wrong"}
    auth_service_mock.login.side_effect = exception

    # Act
    response = client.post("/api/v1/login", json=login_data)

    # Assert
    assert response.status_code == expected_status
    _assert_error_payload(exception, response.json())


def _assert_error_payload(exception: Exception, data: dict[str, Any]) -> None:
    if isinstance(exception, (UserNotFoundException, PasswordVerificationException)):
        _assert_invalid_credentials_error(data)
    else:
        # For generic exceptions, expect a generic code
        assert "error" in data
        error = data["error"]
        assert error.get("code") == "INTERNAL_SERVER_ERROR"


def _assert_invalid_credentials_error(data: dict[str, Any]) -> None:
    assert "error" in data
    error = data["error"]
    assert error.get("code") == "INVALID_CREDENTIALS"
    assert error.get("details") == {}
