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
        detail=_error_response(
            code, message, {"violations": details} if details else None
        ),
    )


def authentication_error(
    message: str, details: Optional[dict[str, Any]] = None
) -> HTTPException:
    """Build a 401 Unauthorized error."""
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=_error_response(ErrorCode.UNAUTHORIZED, message, details),
    )


def forbidden_error(
    message: str, details: Optional[dict[str, Any]] = None
) -> HTTPException:
    """Build a 403 Forbidden error."""
    return HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail=_error_response(ErrorCode.FORBIDDEN, message, details),
    )


def business_rule_violation_error(
    code: str, message: str, details: Optional[dict[str, Any]] = None
) -> HTTPException:
    """Build a 409 Conflict error for business rule violations."""
    return HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail=_error_response(code, message, details),
    )


def unprocessable_entity_error(
    code: str, message: str, details: Optional[dict[str, Any]] = None
) -> HTTPException:
    """Build a 422 Unprocessable Entity error."""
    return HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail=_error_response(code, message, details),
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
        detail=_error_response(ErrorCode.INTERNAL_SERVER_ERROR, message, details),
    )


def _error_response(
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
