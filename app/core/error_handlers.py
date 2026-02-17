from typing import Any, cast

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(HTTPException)
    async def custom_http_exception_handler(  # noqa: F401
        request: Request, exc: HTTPException
    ):  # pylint: disable=unused-function
        # Always wrap the error object under the 'error' key at the root
        if isinstance(exc.detail, dict) and "error" in exc.detail:

            detail_dict = cast(dict[str, Any], exc.detail)
            return JSONResponse(
                status_code=exc.status_code,
                content={"error": detail_dict["error"]},
            )
        # Otherwise, fallback to default behavior
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": exc.detail},
        )
