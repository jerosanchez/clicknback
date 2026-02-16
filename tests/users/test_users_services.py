from typing import Callable
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
def user_repository():
    return create_autospec(UserRepositoryABC)


@pytest.fixture
def user_service(
    enforce_password_complexity: Callable[[str], None],
    hash_password: Callable[[str], str],
    user_repository: Mock,
):
    return UserService(
        enforce_password_complexity=enforce_password_complexity,
        hash_password=hash_password,
        user_repository=user_repository,
    )


def test_create_user_success(
    user_service: UserService, user_repository: Mock, user_factory: Callable[..., User]
):
    # Arrange
    db = Mock(spec=Session)
    user_repository.get_user_by_email.return_value = None
    new_user = user_factory()
    user_repository.add_user.return_value = new_user
    data = {"email": "alice@example.com", "password": "secret"}

    # Act
    returned_user = user_service.create_user(data, db)

    # Assert
    assert returned_user == new_user


def test_create_user_raises_exception_on_email_already_registered(
    user_service: UserService, user_repository: Mock, user_factory: Callable[..., User]
):
    # Arrange
    db = Mock(spec=Session)
    user_repository.get_user_by_email.return_value = user_factory()
    data = {"email": "alice@example.com", "password": "secret"}

    # Act & Assert
    with pytest.raises(EmailAlreadyRegisteredException):
        user_service.create_user(data, db)


def test_create_user_propagates_exception_on_password_not_enough_complex(
    user_service: UserService, enforce_password_complexity: Mock, user_repository: Mock
):
    # Arrange
    db = Mock(spec=Session)
    user_repository.get_user_by_email.return_value = None
    enforce_password_complexity.side_effect = PasswordNotComplexEnoughException(
        "Password not enough complex"
    )
    data = {"email": "alice@example.com", "password": "weak"}

    # Act & Assert
    with pytest.raises(PasswordNotComplexEnoughException):
        user_service.create_user(data, db)
