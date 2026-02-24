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
