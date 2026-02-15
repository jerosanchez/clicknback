from typing import Callable

from app.users.exceptions import EmailAlreadyRegisteredException
from app.users.schemas import UserCreate


class UserService:
    def __init__(
        self,
        enforce_password_complexity: Callable[[str], None],
        hash_password: Callable[[str], str],
    ):
        self.enforce_password_complexity = enforce_password_complexity
        self.hash_password = hash_password

    def create_user(self, create_data: UserCreate):
        _enforce_email_uniqueness(create_data.email)
        self.enforce_password_complexity(create_data.password)

        # TODO: to be stored in the database along with the user data
        _hashed_password = self.hash_password(create_data.password)

        return _hashed_password


def _enforce_email_uniqueness(email: str) -> None:
    # TODO: Simulate email uniqueness check, to be implemented with a real database
    if email == "olduser@example.com":
        raise EmailAlreadyRegisteredException("Email already registered: " + email)
