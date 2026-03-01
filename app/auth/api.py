from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.composition import get_auth_service
from app.auth.exceptions import PasswordVerificationException, UserNotFoundException
from app.auth.models import Token
from app.auth.schemas import Login
from app.auth.services import AuthService
from app.core.database import get_db
from app.core.errors.builders import authentication_error, internal_server_error
from app.core.logging import logging

router = APIRouter(prefix="/auth")


@router.post("/login", response_model=Token)
async def login(
    login_data: Login,
    auth_service: AuthService = Depends(get_auth_service),
    db: Session = Depends(get_db),
) -> Token:
    try:
        return auth_service.login(login_data.model_dump(), db)

    except (UserNotFoundException, PasswordVerificationException):
        raise authentication_error("Invalid email or password.")

    except Exception as e:
        logging.error(
            "An unexpected error occurred during login.", extra={"error": str(e)}
        )
        raise internal_server_error()
