from typing import Any, cast

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

from app.auth.exceptions import InvalidTokenException
from app.core.errors.builders import error_response
from app.core.errors.codes import ErrorCode


def register_error_handlers(app: FastAPI) -> None:

    @app.exception_handler(InvalidTokenException)
    async def invalid_token_exception_handler(
        request: Request, exc: InvalidTokenException
    ):
        return JSONResponse(
            status_code=401,
            content=error_response(
                ErrorCode.INVALID_TOKEN,
                "Invalid or expired token, or user has not the permissions to perform this action.",
                {},
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
