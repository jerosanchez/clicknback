from typing import Any, Callable
from unittest.mock import Mock, create_autospec

import pytest
from sqlalchemy.orm import Session

from app.auth.clients import UsersClientABC
from app.auth.exceptions import PasswordVerificationException, UserNotFoundException
from app.auth.models import Token
from app.auth.services import AuthService
from app.auth.token_provider import OAuth2TokenProviderABC


@pytest.fixture
def db() -> Mock:
    return Mock(spec=Session)


@pytest.fixture
def users_client() -> Mock:
    return create_autospec(UsersClientABC)


@pytest.fixture
def token_provider() -> Mock:
    return create_autospec(OAuth2TokenProviderABC)


@pytest.fixture
def verify_password() -> Mock:
    return Mock()


@pytest.fixture
def auth_service(
    users_client: Mock,
    token_provider: Mock,
    verify_password: Mock,
) -> AuthService:
    return AuthService(
        users_client=users_client,
        token_provider=token_provider,
        verify_password=verify_password,
    )


def test_login_success(
    auth_service: AuthService,
    db: Mock,
    users_client: Mock,
    token_provider: Mock,
    verify_password: Mock,
    user_factory: Callable[..., Any],
) -> None:
    # Arrange
    verify_password.return_value = True
    user = user_factory(id="1", role="user", hashed_password="hashed_pw")
    users_client.get_user_by_email.return_value = user
    token_provider.create_access_token.return_value = "access_token"
    data = {"email": "alice@example.com", "password": "secret"}

    # Act
    token = auth_service.login(data, db)

    # Assert
    assert isinstance(token, Token)
    assert token.access_token == "access_token"
    assert token.token_type == "bearer"


def test_login_raises_exception_on_user_not_found(
    auth_service: AuthService,
    db: Mock,
    users_client: Mock,
) -> None:
    # Arrange
    users_client.get_user_by_email.return_value = None
    data = {"email": "alice@example.com", "password": "secret"}

    # Act & Assert
    with pytest.raises(UserNotFoundException):
        auth_service.login(data, db)


def test_login_raises_exception_on_password_verification(
    auth_service: AuthService,
    db: Mock,
    users_client: Mock,
    verify_password: Mock,
    user_factory: Callable[..., Any],
) -> None:
    # Arrange
    verify_password.return_value = False
    user = user_factory(id="1", role="user", hashed_password="hashed_pw")
    users_client.get_user_by_email.return_value = user
    data = {"email": "alice@example.com", "password": "wrong"}

    # Act & Assert
    with pytest.raises(PasswordVerificationException):
        auth_service.login(data, db)
