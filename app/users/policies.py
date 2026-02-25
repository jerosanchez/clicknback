from re import search as re_search

from app.core.logging import logger
from app.users.exceptions import PasswordNotComplexEnoughException


def enforce_password_complexity(password: str) -> None:
    # TODO: extract these rules to configuration
    if len(password) < 8:
        logger.debug(
            "Password does not meet complexity requirements: too short.",
            extra={"password_length": len(password)},
        )
        raise PasswordNotComplexEnoughException(
            "Password must be at least 8 characters long."
        )
    if not re_search(r"[A-Z]", password):
        logger.debug(
            "Password does not meet complexity requirements: missing uppercase letter."
        )
        raise PasswordNotComplexEnoughException(
            "Password must contain at least one uppercase letter."
        )
    if not re_search(r"[a-z]", password):
        logger.debug(
            "Password does not meet complexity requirements: missing lowercase letter."
        )
        raise PasswordNotComplexEnoughException(
            "Password must contain at least one lowercase letter."
        )
    if not re_search(r"[0-9]", password):
        logger.debug("Password does not meet complexity requirements: missing digit.")
        raise PasswordNotComplexEnoughException(
            "Password must contain at least one digit."
        )
    if not re_search(r"[^A-Za-z0-9]", password):
        logger.debug(
            "Password does not meet complexity requirements: missing special character."
        )
        raise PasswordNotComplexEnoughException(
            "Password must contain at least one special character."
        )
