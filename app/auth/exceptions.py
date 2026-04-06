class UserNotFoundException(Exception):
    def __init__(self, email: str):
        super().__init__(f"User with email '{email}' not found.")
        self.email = email


class PasswordVerificationException(Exception):
    def __init__(self):
        super().__init__("Invalid password.")


class InvalidTokenException(Exception):
    def __init__(self):
        super().__init__("Invalid token.")


class InternalJwtErrorException(Exception):
    def __init__(self):
        super().__init__("An internal error occurred while processing the token.")


class InvalidRefreshTokenException(Exception):
    """Raised when refresh token is invalid, expired, or already used."""

    def __init__(self, reason: str = "Invalid or expired refresh token."):
        super().__init__(reason)
        self.reason = reason


class RefreshTokenAlreadyUsedException(Exception):
    """Raised when attempting to reuse a refresh token (single-use enforcement)."""

    def __init__(self, token_id: str):
        super().__init__(f"Refresh token {token_id} has already been used.")
        self.token_id = token_id
