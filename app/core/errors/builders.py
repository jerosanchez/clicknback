from datetime import datetime
from typing import Any, Optional

from fastapi import HTTPException, status

from app.core.errors.codes import ErrorCode


def validation_error(
    code: str, message: str, details: Optional[list[dict[str, Any]]] = None
) -> HTTPException:
    """Build a 400 Validation Error."""
    return HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=error_response(
            code, message, {"violations": details} if details else None
        ),
    )


def authentication_error(
    message: str, details: Optional[dict[str, Any]] = None
) -> HTTPException:
    """Build a 401 Unauthorized error."""
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=error_response(ErrorCode.INVALID_CREDENTIALS, message, details),
        headers={"WWW-Authenticate": "Bearer"},
    )


def forbidden_error(
    message: str, details: Optional[dict[str, Any]] = None
) -> HTTPException:
    """Build a 403 Forbidden error."""
    return HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail=error_response(ErrorCode.FORBIDDEN, message, details),
    )


def not_found_error(
    message: str, details: Optional[dict[str, Any]] = None
) -> HTTPException:
    """Build a 404 Not Found error."""
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=error_response(ErrorCode.NOT_FOUND, message, details),
    )


def business_rule_violation_error(
    code: str, message: str, details: Optional[dict[str, Any]] = None
) -> HTTPException:
    """Build a 409 Conflict error for business rule violations."""
    return HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail=error_response(code, message, details),
    )


def unprocessable_entity_error(
    code: str, message: str, details: Optional[dict[str, Any]] = None
) -> HTTPException:
    """Build a 422 Unprocessable Entity error."""
    return HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        detail=error_response(code, message, details),
    )


def internal_server_error(
    message: str = "An unexpected error occurred. Our team has been notified. Please retry later.",
    details: Optional[dict[str, Any]] = None,
) -> HTTPException:
    """Build a 500 Internal Server Error."""
    if details is None:
        details = {
            "request_id": "not available",
            "timestamp": datetime.now().isoformat(),
        }
    return HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=error_response(ErrorCode.INTERNAL_SERVER_ERROR, message, details),
    )


def error_response(
    code: str,
    message: str,
    details: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """Build the error response JSON structure."""
    return {
        "error": {
            "code": code,
            "message": message,
            "details": details if details is not None else {},
        }
    }
