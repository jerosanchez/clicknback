from typing import Callable
from unittest.mock import AsyncMock, Mock, create_autospec

import pytest

from app.auth.exceptions import InvalidTokenException, UserInactiveException
from app.auth.models import TokenPayload
from app.auth.token_provider import OAuth2TokenProviderABC
from app.core.current_user import get_current_admin_user, get_current_user
from app.users.models import User, UserRoleEnum
from app.users.repositories import UserRepositoryABC


@pytest.fixture
def db() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def token_provider() -> Mock:
    return create_autospec(OAuth2TokenProviderABC)


@pytest.fixture
def user_repository() -> Mock:
    return create_autospec(UserRepositoryABC)


def build_token_payload(user_role: UserRoleEnum = UserRoleEnum.user) -> TokenPayload:
    return TokenPayload(user_id="admin123", user_role=user_role.value)


# ──────────────────────────────────────────────────────────────────────────────
# get_current_user
# ──────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_current_user_returns_user_on_valid_token(
    db: AsyncMock,
    token_provider: Mock,
    user_repository: Mock,
    user_factory: Callable[..., User],
) -> None:
    # Arrange
    user = user_factory(id="user123", role=UserRoleEnum.user, active=True)
    token_provider.verify_access_token.return_value = build_token_payload(user.role)
    user_repository.get_user_by_id.return_value = user

    # Act
    result = await get_current_user(
        token="token",
        db=db,
        token_provider=token_provider,
        user_repository=user_repository,
    )

    # Assert
    assert result == user


@pytest.mark.asyncio
async def test_get_current_user_raises_on_user_not_found(
    db: AsyncMock,
    token_provider: Mock,
    user_repository: Mock,
) -> None:
    # Arrange
    token_provider.verify_access_token.return_value = build_token_payload()
    user_repository.get_user_by_id.return_value = None

    # Act & Assert
    with pytest.raises(InvalidTokenException):
        await get_current_user(
            token="token",
            db=db,
            token_provider=token_provider,
            user_repository=user_repository,
        )


@pytest.mark.asyncio
async def test_get_current_user_raises_on_inactive_user(
    db: AsyncMock,
    token_provider: Mock,
    user_repository: Mock,
    user_factory: Callable[..., User],
) -> None:
    # Arrange
    inactive_user = user_factory(id="user456", role=UserRoleEnum.user, active=False)
    token_provider.verify_access_token.return_value = build_token_payload(
        inactive_user.role
    )
    user_repository.get_user_by_id.return_value = inactive_user

    # Act & Assert
    with pytest.raises(UserInactiveException):
        await get_current_user(
            token="token",
            db=db,
            token_provider=token_provider,
            user_repository=user_repository,
        )


# ──────────────────────────────────────────────────────────────────────────────
# get_current_admin_user
# ──────────────────────────────────────────────────────────────────────────────


def test_get_current_admin_user_returns_user_on_admin_role(
    user_factory: Callable[..., User],
) -> None:
    # Arrange
    admin_user = user_factory(id="admin123", role=UserRoleEnum.admin, active=True)

    # Act
    result = get_current_admin_user(current_user=admin_user)

    # Assert
    assert result == admin_user


def test_get_current_admin_user_raises_on_non_admin_role(
    user_factory: Callable[..., User],
) -> None:
    # Arrange
    user = user_factory(id="user123", role=UserRoleEnum.user, active=True)

    # Act & Assert
    with pytest.raises(InvalidTokenException):
        get_current_admin_user(current_user=user)
