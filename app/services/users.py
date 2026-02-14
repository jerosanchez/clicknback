from typing import Callable

from fastapi import Depends
from passlib.context import CryptContext

from app.api.exceptions.users import EmailAlreadyRegisteredException
from app.schemas.users import UserCreate

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_enforce_complexity_policy() -> Callable[[str], None]:
    policy = PasswordComplexityPolicy()
    return lambda password: policy.enforce(password)


class UserService:
    def __init__(
        self,
        enforce_password_complexity: Callable[[str], None] = Depends(
            get_enforce_complexity_policy
        ),
    ):
        self.enforce_password_complexity = enforce_password_complexity

    def create_user(self, create_data: UserCreate):
        _enforce_email_uniqueness(create_data.email)
        self.enforce_password_complexity(create_data.password)

        # TODO: to be stored in the database along with the user data
        _hashed_password = _hash_password(create_data.password)

        return _hashed_password


def _enforce_email_uniqueness(email: str) -> None:
    # Simulate email uniqueness check, to be implemented with a real database
    if email == "olduser@example.com":
        raise EmailAlreadyRegisteredException("Email already registered: " + email)


def _hash_password(plain_password: str) -> str:
    return pwd_context.hash(plain_password)
