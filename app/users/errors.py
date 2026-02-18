from enum import Enum


class ErrorCode(str, Enum):
    """Semantic error codes used in the Users API."""

    # 400 - Bad Request (Validation errors)
    PASSWORD_NOT_COMPLEX_ENOUGH = "PASSWORD_NOT_COMPLEX_ENOUGH"

    # 409 - Conflict (Business rule violations)
    EMAIL_ALREADY_REGISTERED = "EMAIL_ALREADY_REGISTERED"
