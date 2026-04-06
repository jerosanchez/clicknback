from datetime import datetime

from app.auth.clients import UsersClientABC
from app.auth.exceptions import (
    InvalidRefreshTokenException,
    PasswordVerificationException,
    RefreshTokenAlreadyUsedException,
    UserNotFoundException,
)
from app.core.logging import logger


def enforce_user_exists(user: UsersClientABC | None, email: str) -> None:
    """Raise if the user does not exist by email.

    Args:
        user: The user DTO or None if not found
        email: The email address being looked up

    Raises:
        UserNotFoundException: If user is None
    """
    if user is None:
        logger.warning(
            "Login attempt with non-existent email (potential enumeration attack).",
            extra={"email": email},
        )
        raise UserNotFoundException(email)


def enforce_password_valid(password_correct: bool) -> None:
    """Raise if the password verification failed.

    Args:
        password_correct: Result of password comparison

    Raises:
        PasswordVerificationException: If password does not match
    """
    if not password_correct:
        logger.warning(
            "Login attempt with incorrect password (potential brute force attack)."
        )
        raise PasswordVerificationException()


def enforce_refresh_token_exists(token: object | None, user_id: str) -> None:
    """Raise if the refresh token does not exist in the database.

    Args:
        token: The token object from the database or None if not found
        user_id: The user ID associated with the token

    Raises:
        InvalidRefreshTokenException: If token is None
    """
    if token is None:
        logger.warning(
            "Valid JWT but refresh token not found in database "
            "(potential token tampering or man-in-the-middle attack).",
            extra={"user_id": user_id},
        )
        raise InvalidRefreshTokenException("Token not found.")


def enforce_refresh_token_not_expired(token: object, now: datetime) -> None:
    """Raise if the refresh token has expired.

    Args:
        token: The token object with is_expired() method
        now: Current datetime for expiration check

    Raises:
        InvalidRefreshTokenException: If token is expired
    """
    if token.is_expired(now):  # type: ignore
        logger.warning(
            "Attempted to refresh with expired token.",
            extra={"token_id": token.id},  # type: ignore
        )
        raise InvalidRefreshTokenException("Refresh token has expired.")


def enforce_refresh_token_not_used(token: object) -> None:
    """Raise if the refresh token has already been used (single-use enforcement).

    Args:
        token: The token object with is_used() method

    Raises:
        RefreshTokenAlreadyUsedException: If token has been used
    """
    if token.is_used():  # type: ignore
        logger.warning(
            "Attempted to reuse refresh token (single-use enforcement violated "
            "- potential token replay attack or compromised client).",
            extra={"token_id": token.id},  # type: ignore
        )
        raise RefreshTokenAlreadyUsedException(token.id)  # type: ignore


def enforce_user_exists_for_refresh(user: object | None, user_id: str) -> None:
    """Raise if the user does not exist during token refresh.

    Args:
        user: The user DTO or None if not found
        user_id: The user ID being looked up

    Raises:
        InvalidRefreshTokenException: If user is None
    """
    if user is None:
        logger.error(
            "User not found during token refresh (data inconsistency - "
            "user may have been deleted after token issue).",
            extra={"user_id": user_id},
        )
        raise InvalidRefreshTokenException("User not found.")
