from enum import Enum


class ErrorCode(str, Enum):
    """Semantic error codes used across the API."""

    # 400 - Bad Request (Validation errors)
    VALIDATION_ERROR = "VALIDATION_ERROR"

    # 401 - Unauthorized
    INVALID_CREDENTIALS = "INVALID_CREDENTIALS"
    INVALID_TOKEN = "INVALID_TOKEN"
    EXPIRED_TOKEN = "EXPIRED_TOKEN"
    INVALID_REFRESH_TOKEN = "INVALID_REFRESH_TOKEN"
    EXPIRED_REFRESH_TOKEN = "EXPIRED_REFRESH_TOKEN"
    TOKEN_REVOKED = "TOKEN_REVOKED"
    USER_INACTIVE = "USER_INACTIVE"

    # 403 - Forbidden
    FORBIDDEN = "FORBIDDEN"

    # 404 - Not Found
    NOT_FOUND = "NOT_FOUND"

    # 409 - Conflict (Business rule violations)

    # 422 - Unprocessable Entity (Semantically invalid requests)

    # 500 - Internal Server Error
    INTERNAL_SERVER_ERROR = "INTERNAL_SERVER_ERROR"
