class UserNotFoundException(Exception):
    def __init__(self, email: str):
        super().__init__(f"User with email '{email}' not found.")
        self.email = email


class PasswordVerificationException(Exception):
    def __init__(self):
        super().__init__("Invalid password.")
