from datetime import datetime, timezone
from typing import Any, Callable
from unittest.mock import AsyncMock, Mock, create_autospec

import pytest

from app.auth import policies
from app.auth.clients import UsersClientABC
from app.auth.exceptions import (
    InvalidRefreshTokenException,
    RefreshTokenAlreadyUsedException,
)
from app.auth.models import TokenResponse
from app.auth.repositories import RefreshTokenRepositoryABC
from app.auth.services import AuthService
from app.auth.token_provider import OAuth2TokenProviderABC
from app.core.unit_of_work import UnitOfWorkABC


@pytest.fixture
def uow() -> Mock:
    """Mock UnitOfWorkABC with async session and commit."""
    mock_uow = Mock(spec=UnitOfWorkABC)
    mock_uow.session = AsyncMock()
    mock_uow.commit = AsyncMock()
    return mock_uow


@pytest.fixture
def users_client() -> Mock:
    return create_autospec(UsersClientABC)


@pytest.fixture
def token_provider() -> Mock:
    return create_autospec(OAuth2TokenProviderABC)


@pytest.fixture
def refresh_token_repository() -> Mock:
    return create_autospec(RefreshTokenRepositoryABC)


@pytest.fixture
def verify_password() -> Mock:
    return Mock()


@pytest.fixture
def auth_service(
    users_client: Mock,
    token_provider: Mock,
    refresh_token_repository: Mock,
    verify_password: Mock,
) -> AuthService:
    return AuthService(
        users_client=users_client,
        token_provider=token_provider,
        refresh_token_repository=refresh_token_repository,
        verify_password=verify_password,
    )


def _login_input_data() -> dict[str, Any]:
    return {"email": "alice@example.com", "password": "ValidPass1!"}


# ──────────────────────────────────────────────────────────────────────────────
# AuthService.login
# ──────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_login_returns_token_response_on_success(
    auth_service: AuthService,
    uow: Mock,
    users_client: Mock,
    token_provider: Mock,
    refresh_token_repository: Mock,
    verify_password: Mock,
    user_factory: Callable[..., Any],
) -> None:
    # Arrange
    verify_password.return_value = True
    users_client.get_user_by_email.return_value = user_factory()
    token_provider.create_access_token.return_value = "access_token"
    token_provider.create_refresh_token.return_value = "refresh_token"
    token_provider.hash_refresh_token.return_value = "hash_token"
    token_provider.refresh_ttl_in_minutes = 43200
    refresh_token_repository.create = AsyncMock()

    # Act
    response = await auth_service.login(_login_input_data(), uow)

    # Assert
    assert isinstance(response, TokenResponse)
    assert response.access_token == "access_token"
    assert response.refresh_token == "refresh_token"
    assert response.token_type == "bearer"
    refresh_token_repository.create.assert_called_once()
    uow.commit.assert_called_once()


@pytest.mark.asyncio
async def test_login_calls_enforce_user_exists_policy(
    auth_service: AuthService,
    uow: Mock,
    users_client: Mock,
) -> None:
    # Arrange
    users_client.get_user_by_email.return_value = None

    # Act & Assert — policy will raise the exception
    from app.auth.exceptions import UserNotFoundException

    with pytest.raises(UserNotFoundException):
        await auth_service.login(_login_input_data(), uow)


@pytest.mark.asyncio
async def test_login_calls_enforce_password_valid_policy(
    auth_service: AuthService,
    uow: Mock,
    users_client: Mock,
    verify_password: Mock,
    user_factory: Callable[..., Any],
) -> None:
    # Arrange
    verify_password.return_value = False
    users_client.get_user_by_email.return_value = user_factory()

    # Act & Assert — policy will raise the exception
    from app.auth.exceptions import PasswordVerificationException

    with pytest.raises(PasswordVerificationException):
        await auth_service.login(_login_input_data(), uow)


# ──────────────────────────────────────────────────────────────────────────────
# AuthService.refresh
# ──────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_refresh_returns_new_tokens_on_success(
    auth_service: AuthService,
    uow: Mock,
    users_client: Mock,
    token_provider: Mock,
    refresh_token_repository: Mock,
    user_factory: Callable[..., Any],
) -> None:
    # Arrange
    user = user_factory()
    refresh_token = "valid_refresh_token"
    token_hash = "hashed_token"

    # Mock token provider methods
    token_provider.verify_refresh_token.return_value = user.id
    token_provider.hash_refresh_token.return_value = token_hash
    token_provider.refresh_ttl_in_minutes = 43200
    token_provider.create_access_token.return_value = "new_access_token"
    token_provider.create_refresh_token.return_value = "new_refresh_token"

    # Mock repository methods
    refresh_token_repository.get_by_hash = AsyncMock(
        return_value=Mock(
            id="token_id",
            user_id=user.id,
            is_expired=Mock(return_value=False),
            is_used=Mock(return_value=False),
        )
    )
    refresh_token_repository.mark_as_used = AsyncMock()
    refresh_token_repository.create = AsyncMock()

    # Mock users client
    users_client.get_user_by_id = AsyncMock(return_value=user)

    # Act
    response = await auth_service.refresh(refresh_token, uow)

    # Assert
    assert isinstance(response, TokenResponse)
    assert response.access_token == "new_access_token"
    assert response.refresh_token == "new_refresh_token"
    assert response.token_type == "bearer"
    refresh_token_repository.mark_as_used.assert_called_once()
    refresh_token_repository.create.assert_called_once()
    uow.commit.assert_called_once()


@pytest.mark.asyncio
async def test_refresh_raises_on_invalid_token_signature(
    auth_service: AuthService,
    uow: Mock,
    token_provider: Mock,
) -> None:
    # Arrange
    refresh_token = "invalid_token"
    token_provider.verify_refresh_token.side_effect = InvalidRefreshTokenException()

    # Act & Assert
    with pytest.raises(InvalidRefreshTokenException):
        await auth_service.refresh(refresh_token, uow)


@pytest.mark.asyncio
async def test_refresh_enforces_refresh_token_exists_policy(
    auth_service: AuthService,
    uow: Mock,
    token_provider: Mock,
    refresh_token_repository: Mock,
) -> None:
    # Arrange
    refresh_token = "valid_jwt_but_not_in_db"
    user_id = "user-123"
    token_hash = "hashed_token"

    token_provider.verify_refresh_token.return_value = user_id
    token_provider.hash_refresh_token.return_value = token_hash
    refresh_token_repository.get_by_hash = AsyncMock(return_value=None)

    # Act & Assert — policy will raise the exception
    with pytest.raises(InvalidRefreshTokenException):
        await auth_service.refresh(refresh_token, uow)


@pytest.mark.asyncio
async def test_refresh_enforces_refresh_token_not_expired_policy(
    auth_service: AuthService,
    uow: Mock,
    token_provider: Mock,
    refresh_token_repository: Mock,
) -> None:
    # Arrange
    refresh_token = "expired_token"
    user_id = "user-123"
    token_hash = "hashed_token"

    mock_token = Mock(
        id="token_id",
        user_id=user_id,
        is_expired=Mock(return_value=True),
        is_used=Mock(return_value=False),
    )

    token_provider.verify_refresh_token.return_value = user_id
    token_provider.hash_refresh_token.return_value = token_hash
    refresh_token_repository.get_by_hash = AsyncMock(return_value=mock_token)

    # Act & Assert — policy will raise the exception
    with pytest.raises(InvalidRefreshTokenException):
        await auth_service.refresh(refresh_token, uow)


@pytest.mark.asyncio
async def test_refresh_enforces_refresh_token_not_used_policy(
    auth_service: AuthService,
    uow: Mock,
    token_provider: Mock,
    refresh_token_repository: Mock,
) -> None:
    # Arrange
    refresh_token = "already_used_token"
    user_id = "user-123"
    token_hash = "hashed_token"

    mock_token = Mock(
        id="token_id",
        user_id=user_id,
        is_expired=Mock(return_value=False),
        is_used=Mock(return_value=True),
    )

    token_provider.verify_refresh_token.return_value = user_id
    token_provider.hash_refresh_token.return_value = token_hash
    refresh_token_repository.get_by_hash = AsyncMock(return_value=mock_token)

    # Act & Assert — policy will raise the exception
    with pytest.raises(RefreshTokenAlreadyUsedException):
        await auth_service.refresh(refresh_token, uow)


@pytest.mark.asyncio
async def test_refresh_enforces_user_exists_for_refresh_policy(
    auth_service: AuthService,
    uow: Mock,
    token_provider: Mock,
    refresh_token_repository: Mock,
    users_client: Mock,
) -> None:
    # Arrange
    refresh_token = "valid_token"
    user_id = "user-123"
    token_hash = "hashed_token"

    mock_token = Mock(
        id="token_id",
        user_id=user_id,
        is_expired=Mock(return_value=False),
        is_used=Mock(return_value=False),
    )

    token_provider.verify_refresh_token.return_value = user_id
    token_provider.hash_refresh_token.return_value = token_hash
    refresh_token_repository.get_by_hash = AsyncMock(return_value=mock_token)
    users_client.get_user_by_id = AsyncMock(return_value=None)

    # Act & Assert — policy will raise the exception
    with pytest.raises(InvalidRefreshTokenException):
        await auth_service.refresh(refresh_token, uow)
