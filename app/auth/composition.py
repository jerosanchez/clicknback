from typing import Callable

from fastapi import Depends
from passlib.context import CryptContext

from app.auth.clients import UsersClient
from app.auth.services import AuthService
from app.auth.token_provider import JwtOAuth2TokenProvider, OAuth2TokenProviderABC
from app.core.config import settings
from app.users.repositories import UserRepository

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_users_client(user_repository: UserRepository = Depends()):
    return UsersClient(user_repository)


def get_token_provider():
    return JwtOAuth2TokenProvider(settings.oauth_token_ttl)


def get_password_verifier() -> Callable[[str, str], bool]:
    return pwd_context.verify


def get_auth_service(
    users_client: UsersClient = Depends(get_users_client),
    token_provider: OAuth2TokenProviderABC = Depends(get_token_provider),
    verify_password: Callable[[str, str], bool] = Depends(get_password_verifier),
):
    return AuthService(users_client, token_provider, verify_password)
