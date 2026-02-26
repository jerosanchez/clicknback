from typing import Any, Callable
from unittest.mock import Mock, create_autospec

import pytest
from sqlalchemy.orm import Session

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


def test_create_user_success(
    user_service: UserService,
    user_repository: Mock,
    user_factory: Callable[..., User],
    user_input_data: Callable[[User], dict[str, Any]],
) -> None:
    # Arrange
    db = Mock(spec=Session)
    new_user = user_factory()
    user_repository.get_user_by_email.return_value = None
    user_repository.add_user.return_value = new_user
    data = user_input_data(new_user)

    # Act
    returned_user = user_service.create_user(data, db)

    # Assert
    assert returned_user == new_user


def test_create_user_raises_exception_on_email_already_registered(
    user_service: UserService,
    user_repository: Mock,
    user_factory: Callable[..., User],
    user_input_data: Callable[[User], dict[str, Any]],
) -> None:
    # Arrange
    db = Mock(spec=Session)
    existing_user = user_factory()
    user_repository.get_user_by_email.return_value = existing_user
    data = user_input_data(existing_user)

    # Act & Assert
    with pytest.raises(EmailAlreadyRegisteredException):
        user_service.create_user(data, db)


def test_create_user_propagates_exception_on_password_not_enough_complex(
    user_service: UserService,
    enforce_password_complexity: Mock,
    user_repository: Mock,
    user_factory: Callable[..., User],
    user_input_data: Callable[[User], dict[str, Any]],
) -> None:
    # Arrange
    db = Mock(spec=Session)
    user_repository.get_user_by_email.return_value = None
    enforce_password_complexity.side_effect = PasswordNotComplexEnoughException(
        "Password not enough complex"
    )
    data = user_input_data(user_factory())

    # Act & Assert
    with pytest.raises(PasswordNotComplexEnoughException):
        user_service.create_user(data, db)
