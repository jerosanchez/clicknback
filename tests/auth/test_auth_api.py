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
from app.core.errors.codes import ErrorCode
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


def _login_input_data() -> dict[str, Any]:
    return {"email": "alice@example.com", "password": "ValidPass1!"}


def _assert_token_out_response(data: dict[str, Any], token: Token) -> None:
    assert data["access_token"] == token.access_token
    assert data["token_type"] == token.token_type


def _assert_error_payload(data: dict[str, Any], expected_code: ErrorCode) -> None:
    assert "error" in data
    assert data["error"]["code"] == expected_code


# ──────────────────────────────────────────────────────────────────────────────
# POST /api/v1/login
# ──────────────────────────────────────────────────────────────────────────────


def test_login_returns_200_on_success(
    client: TestClient, auth_service_mock: Mock
) -> None:
    # Arrange
    token = Token(access_token="some.jwt.token", token_type="bearer")
    auth_service_mock.login.return_value = token

    # Act
    response = client.post("/api/v1/login", json=_login_input_data())

    # Assert
    assert response.status_code == status.HTTP_200_OK
    _assert_token_out_response(response.json(), token)


@pytest.mark.parametrize(
    "exception,expected_status,expected_code",
    [
        (
            UserNotFoundException("alice@example.com"),
            status.HTTP_401_UNAUTHORIZED,
            ErrorCode.INVALID_CREDENTIALS,
        ),
        (
            PasswordVerificationException(),
            status.HTTP_401_UNAUTHORIZED,
            ErrorCode.INVALID_CREDENTIALS,
        ),
        (
            Exception("Something broke"),
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            ErrorCode.INTERNAL_SERVER_ERROR,
        ),
    ],
)
def test_login_returns_error_on_exception(
    client: TestClient,
    auth_service_mock: Mock,
    exception: Exception,
    expected_status: int,
    expected_code: ErrorCode,
) -> None:
    # Arrange
    auth_service_mock.login.side_effect = exception

    # Act
    response = client.post("/api/v1/login", json=_login_input_data())

    # Assert
    assert response.status_code == expected_status
    _assert_error_payload(response.json(), expected_code)
