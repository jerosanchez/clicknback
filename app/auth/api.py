from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.clients import UserClient
from app.auth.exceptions import UserNotFoundException
from app.auth.models import Token
from app.auth.providers import JwtOAuth2TokenProvider, OAuth2TokenProviderABC
from app.auth.schemas import Login
from app.auth.services import AuthService
from app.core.database import get_db
from app.core.errors.builders import authentication_error, internal_server_error
from app.users.repositories import UserRepository

router = APIRouter(prefix="/api/v1")


def get_users_client(user_repository: UserRepository = Depends()):
    return UserClient(user_repository)


def get_token_provider():
    return JwtOAuth2TokenProvider()


def get_auth_service(
    users_client: UserClient = Depends(get_users_client),
    token_provider: OAuth2TokenProviderABC = Depends(get_token_provider),
):
    return AuthService(users_client, token_provider)


@router.post("/login", response_model=Token)
async def login(
    login_data: Login,
    auth_service: AuthService = Depends(get_auth_service),
    db: Session = Depends(get_db),
) -> Token:
    try:
        return auth_service.login(login_data.model_dump(), db)

    except UserNotFoundException:
        raise authentication_error("Invalid email or password.")

    except Exception:
        raise internal_server_error()
