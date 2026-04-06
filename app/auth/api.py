from fastapi import APIRouter, Depends, HTTPException, status

from app.auth.composition import get_auth_service, get_unit_of_work
from app.auth.exceptions import (
    InvalidRefreshTokenException,
    PasswordVerificationException,
    RefreshTokenAlreadyUsedException,
    UserNotFoundException,
)
from app.auth.schemas import Login, RefreshTokenRequest, TokenResponse
from app.auth.services import AuthService
from app.core.errors.builders import (
    authentication_error,
    error_response,
    internal_server_error,
)
from app.core.errors.codes import ErrorCode
from app.core.logging import logging
from app.core.unit_of_work import UnitOfWorkABC

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/login",
    response_model=TokenResponse,
    description="Authenticate a user and return access and refresh tokens.",
    status_code=200,
)
async def login(
    login_data: Login,
    auth_service: AuthService = Depends(get_auth_service),
    uow: UnitOfWorkABC = Depends(get_unit_of_work),
) -> TokenResponse:
    try:
        return await auth_service.login(login_data.model_dump(), uow)

    except (UserNotFoundException, PasswordVerificationException):
        raise authentication_error("Invalid email or password.")

    except Exception as e:
        logging.error(
            "An unexpected error occurred during login.", extra={"error": str(e)}
        )
        raise internal_server_error()


@router.post(
    "/refresh",
    response_model=TokenResponse,
    description="Refresh an expired access token using a refresh token.",
    status_code=200,
)
async def refresh(
    request: RefreshTokenRequest,
    auth_service: AuthService = Depends(get_auth_service),
    uow: UnitOfWorkABC = Depends(get_unit_of_work),
) -> TokenResponse:
    try:
        return await auth_service.refresh(request.refresh_token, uow)

    except RefreshTokenAlreadyUsedException:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=error_response(
                ErrorCode.TOKEN_REVOKED,
                "Refresh token has been revoked. Please log in again.",
                {},
            ),
            headers={"WWW-Authenticate": "Bearer"},
        )

    except InvalidRefreshTokenException:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=error_response(
                ErrorCode.INVALID_REFRESH_TOKEN,
                "Invalid or expired refresh token.",
                {},
            ),
            headers={"WWW-Authenticate": "Bearer"},
        )

    except Exception as e:
        logging.error(
            "An unexpected error occurred during token refresh.",
            extra={"error": str(e)},
        )
        raise internal_server_error()
