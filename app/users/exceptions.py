class EmailAlreadyRegisteredException(Exception):
    def __init__(self, email: str):
        super().__init__(f"Email '{email}' is already registered.")
        self.email = email


class PasswordNotComplexEnoughException(Exception):
    def __init__(self, reason: str):
        super().__init__(f"Password is not complex enough: {reason}")
        self.reason = reason
