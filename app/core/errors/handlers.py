from typing import Any, cast

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

from app.auth.exceptions import (
    ExpiredRefreshTokenException,
    ExpiredTokenException,
    InvalidTokenException,
    RefreshTokenAlreadyUsedException,
    UserInactiveException,
)
from app.core.errors.builders import error_response
from app.core.errors.codes import ErrorCode


def register_error_handlers(app: FastAPI) -> None:

    @app.exception_handler(ExpiredTokenException)
    async def expired_token_exception_handler(
        request: Request, exc: ExpiredTokenException
    ):
        return JSONResponse(
            status_code=401,
            content=error_response(
                ErrorCode.EXPIRED_TOKEN,
                "Access token has expired. Please refresh your token.",
                {},
            ),
            headers={"WWW-Authenticate": "Bearer"},
        )

    @app.exception_handler(InvalidTokenException)
    async def invalid_token_exception_handler(
        request: Request, exc: InvalidTokenException
    ):
        return JSONResponse(
            status_code=401,
            content=error_response(
                ErrorCode.INVALID_TOKEN,
                "Invalid token, or user does not have permissions to perform this action.",
                {},
            ),
            headers={"WWW-Authenticate": "Bearer"},
        )

    @app.exception_handler(UserInactiveException)
    async def user_inactive_exception_handler(
        request: Request, exc: UserInactiveException
    ):
        return JSONResponse(
            status_code=401,
            content=error_response(
                ErrorCode.USER_INACTIVE,
                "User account is inactive.",
                {"user_id": exc.user_id},
            ),
            headers={"WWW-Authenticate": "Bearer"},
        )

    @app.exception_handler(ExpiredRefreshTokenException)
    async def expired_refresh_token_exception_handler(
        request: Request, exc: ExpiredRefreshTokenException
    ):
        return JSONResponse(
            status_code=401,
            content=error_response(
                ErrorCode.EXPIRED_REFRESH_TOKEN,
                "Refresh token has expired. Please log in again.",
                {},
            ),
            headers={"WWW-Authenticate": "Bearer"},
        )

    @app.exception_handler(RefreshTokenAlreadyUsedException)
    async def refresh_token_already_used_exception_handler(
        request: Request, exc: RefreshTokenAlreadyUsedException
    ):
        return JSONResponse(
            status_code=401,
            content=error_response(
                ErrorCode.TOKEN_REVOKED,
                "Refresh token has been revoked. Please log in again.",
                {"token_id": exc.token_id},
            ),
            headers={"WWW-Authenticate": "Bearer"},
        )

    @app.exception_handler(HTTPException)
    async def custom_http_exception_handler(
        request: Request, exc: HTTPException
    ):  # pylint: disable=unused-function
        # Always wrap the error object under the 'error' key at the root
        if isinstance(exc.detail, dict) and "error" in exc.detail:

            detail_dict = cast(dict[str, Any], exc.detail)
            return JSONResponse(
                status_code=exc.status_code,
                content={"error": detail_dict["error"]},
            )

        return JSONResponse(
            status_code=exc.status_code,
            content={"error": exc.detail},
        )
