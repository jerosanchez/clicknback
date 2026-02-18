from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.errors.builders import authentication_error, internal_server_error
from app.users.repositories import UserRepository

from .clients import UserClient
from .exceptions import UserNotFoundException
from .models import Token
from .schemas import Login
from .services import AuthService

router = APIRouter(prefix="/api/v1")


def get_user_client(user_repository: UserRepository = Depends()):
    return UserClient(user_repository)


def get_auth_service(user_client: UserClient = Depends(get_user_client)):
    return AuthService(user_client)


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
