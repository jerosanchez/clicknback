from typing import Any, Callable
from unittest.mock import AsyncMock, Mock, create_autospec

import pytest

from app.users.exceptions import (
    EmailAlreadyRegisteredException,
    PasswordNotComplexEnoughException,
)
from app.users.models import User
from app.users.repositories import UserRepositoryABC
from app.users.services import UserService


@pytest.fixture
def enforce_password_complexity() -> Callable[[str], None]:
    return Mock()


@pytest.fixture
def hash_password() -> Callable[[str], str]:
    return Mock(return_value="hashed_pw")


@pytest.fixture
def user_repository() -> Mock:
    return create_autospec(UserRepositoryABC)


@pytest.fixture
def user_service(
    enforce_password_complexity: Callable[[str], None],
    hash_password: Callable[[str], str],
    user_repository: Mock,
) -> UserService:
    return UserService(
        enforce_password_complexity=enforce_password_complexity,
        hash_password=hash_password,
        user_repository=user_repository,
    )


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────


def _make_uow() -> Mock:
    """Create a fresh mock UnitOfWork for write service tests."""
    uow = Mock()
    uow.session = AsyncMock()
    uow.commit = AsyncMock()
    uow.rollback = AsyncMock()
    return uow


# ──────────────────────────────────────────────────────────────────────────────
# UserService.create_user
# ──────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_user_returns_user_on_success(
    user_service: UserService,
    user_repository: Mock,
    user_factory: Callable[..., User],
    user_input_data: Callable[[User], dict[str, Any]],
) -> None:
    # Arrange
    uow = _make_uow()
    new_user = user_factory()
    user_repository.get_user_by_email.return_value = None
    user_repository.add_user.return_value = new_user
    data = user_input_data(new_user)

    # Act
    returned_user = await user_service.create_user(data, uow)

    # Assert
    assert returned_user == new_user
    uow.commit.assert_called_once()


@pytest.mark.asyncio
async def test_create_user_raises_on_email_already_registered(
    user_service: UserService,
    user_repository: Mock,
    user_factory: Callable[..., User],
    user_input_data: Callable[[User], dict[str, Any]],
) -> None:
    # Arrange
    uow = _make_uow()
    existing_user = user_factory()
    user_repository.get_user_by_email.return_value = existing_user
    data = user_input_data(existing_user)

    # Act & Assert
    with pytest.raises(EmailAlreadyRegisteredException):
        await user_service.create_user(data, uow)

    uow.commit.assert_not_called()


@pytest.mark.asyncio
async def test_create_user_raises_on_password_not_complex_enough(
    user_service: UserService,
    enforce_password_complexity: Mock,
    user_repository: Mock,
    user_factory: Callable[..., User],
    user_input_data: Callable[[User], dict[str, Any]],
) -> None:
    # Arrange
    uow = _make_uow()
    user_repository.get_user_by_email.return_value = None
    enforce_password_complexity.side_effect = PasswordNotComplexEnoughException(
        "Password not enough complex"
    )
    data = user_input_data(user_factory())

    # Act & Assert
    with pytest.raises(PasswordNotComplexEnoughException):
        await user_service.create_user(data, uow)

    uow.commit.assert_not_called()
