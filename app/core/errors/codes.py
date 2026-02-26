from enum import Enum


class ErrorCode(str, Enum):
    """Semantic error codes used across the API."""

    # 400 - Bad Request (Validation errors)
    VALIDATION_ERROR = "VALIDATION_ERROR"

    # 401 - Unauthorized
    INVALID_CREDENTIALS = "INVALID_CREDENTIALS"
    INVALID_TOKEN = "INVALID_TOKEN"

    # 403 - Forbidden
    FORBIDDEN = "FORBIDDEN"

    # 409 - Conflict (Business rule violations)

    # 422 - Unprocessable Entity (Semantically invalid requests)

    # 500 - Internal Server Error
    INTERNAL_SERVER_ERROR = "INTERNAL_SERVER_ERROR"
