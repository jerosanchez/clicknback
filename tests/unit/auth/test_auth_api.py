from typing import Any, AsyncGenerator, Generator
from unittest.mock import AsyncMock, Mock, create_autospec

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.auth.composition import get_auth_service, get_unit_of_work
from app.auth.exceptions import (
    InvalidRefreshTokenException,
    PasswordVerificationException,
    RefreshTokenAlreadyUsedException,
    UserNotFoundException,
)
from app.auth.models import TokenResponse
from app.auth.services import AuthService
from app.core.database import get_async_db
from app.core.errors.codes import ErrorCode
from app.core.unit_of_work import UnitOfWorkABC
from app.main import app


@pytest.fixture
def auth_service_mock() -> Mock:
    return create_autospec(AuthService)


@pytest.fixture
def unit_of_work_mock() -> Mock:
    """Mock UnitOfWorkABC for dependency injection."""
    mock_uow = Mock(spec=UnitOfWorkABC)
    mock_uow.session = AsyncMock()
    mock_uow.commit = AsyncMock()
    return mock_uow


async def _mock_get_async_db() -> AsyncGenerator[AsyncMock, Any]:
    yield AsyncMock()


@pytest.fixture
def client(
    auth_service_mock: Mock, unit_of_work_mock: Mock
) -> Generator[TestClient, None, None]:
    app.dependency_overrides[get_async_db] = _mock_get_async_db
    app.dependency_overrides[get_auth_service] = lambda: auth_service_mock
    app.dependency_overrides[get_unit_of_work] = lambda: unit_of_work_mock

    test_client = TestClient(app)
    yield test_client

    app.dependency_overrides.clear()


def _login_input_data() -> dict[str, Any]:
    return {"email": "alice@example.com", "password": "ValidPass1!"}


def _assert_token_response(data: dict[str, Any], response: TokenResponse) -> None:
    assert data["access_token"] == response.access_token
    assert data["refresh_token"] == response.refresh_token
    assert data["token_type"] == response.token_type


def _assert_error_payload(data: dict[str, Any], expected_code: ErrorCode) -> None:
    assert "error" in data
    assert data["error"]["code"] == expected_code


# ──────────────────────────────────────────────────────────────────────────────
# POST /api/v1/auth/login
# ──────────────────────────────────────────────────────────────────────────────


def test_login_returns_200_on_success(
    client: TestClient, auth_service_mock: Mock
) -> None:
    # Arrange
    token_response = TokenResponse(
        access_token="some.jwt.token",
        refresh_token="some.refresh.token",
        token_type="bearer",
    )
    auth_service_mock.login.return_value = token_response

    # Act
    response = client.post("/api/v1/auth/login", json=_login_input_data())

    # Assert
    assert response.status_code == status.HTTP_200_OK
    _assert_token_response(response.json(), token_response)


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
    response = client.post("/api/v1/auth/login", json=_login_input_data())

    # Assert
    assert response.status_code == expected_status
    _assert_error_payload(response.json(), expected_code)


# ──────────────────────────────────────────────────────────────────────────────
# POST /api/v1/auth/refresh
# ──────────────────────────────────────────────────────────────────────────────


def test_refresh_returns_200_with_new_tokens_on_success(
    client: TestClient, auth_service_mock: Mock
) -> None:
    # Arrange
    token_response = TokenResponse(
        access_token="new.access.token",
        refresh_token="new.refresh.token",
        token_type="bearer",
    )
    auth_service_mock.refresh.return_value = token_response
    refresh_input = {"refresh_token": "old.refresh.token"}

    # Act
    response = client.post("/api/v1/auth/refresh", json=refresh_input)

    # Assert
    assert response.status_code == status.HTTP_200_OK
    _assert_token_response(response.json(), token_response)
    auth_service_mock.refresh.assert_called_once()


@pytest.mark.parametrize(
    "exception,expected_status,expected_code",
    [
        (
            InvalidRefreshTokenException(),
            status.HTTP_401_UNAUTHORIZED,
            ErrorCode.INVALID_REFRESH_TOKEN,
        ),
        (
            RefreshTokenAlreadyUsedException("token-id"),
            status.HTTP_401_UNAUTHORIZED,
            ErrorCode.INVALID_REFRESH_TOKEN,
        ),
        (
            Exception("Unexpected error"),
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            ErrorCode.INTERNAL_SERVER_ERROR,
        ),
    ],
)
def test_refresh_returns_error_on_exception(
    client: TestClient,
    auth_service_mock: Mock,
    exception: Exception,
    expected_status: int,
    expected_code: ErrorCode,
) -> None:
    # Arrange
    auth_service_mock.refresh.side_effect = exception
    refresh_input = {"refresh_token": "invalid.token"}

    # Act
    response = client.post("/api/v1/auth/refresh", json=refresh_input)

    # Assert
    assert response.status_code == expected_status
    _assert_error_payload(response.json(), expected_code)
