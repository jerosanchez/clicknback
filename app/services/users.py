from re import search as re_search

from passlib.context import CryptContext

from app.schemas.users import UserCreate

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class PasswordNotComplexEnoughException(Exception):
    pass


class EmailAlreadyRegisteredException(Exception):
    pass


class UserService:
    def __init__(self):
        pass

    def create_user(self, create_data: UserCreate):
        _enforce_email_uniqueness(create_data.email)
        _enforce_password_complexity(create_data.password)

        # TODO: to be stored in the database along with the user data
        _hashed_password = _hash_password(create_data.password)

        return _hashed_password


def _enforce_email_uniqueness(email: str) -> None:
    # Simulate email uniqueness check, to be implemented with a real database
    if email == "olduser@example.com":
        raise EmailAlreadyRegisteredException("Email already registered: " + email)


def _enforce_password_complexity(password: str) -> None:
    if len(password) < 8:
        raise PasswordNotComplexEnoughException(
            "Password must be at least 8 characters long."
        )
    if not re_search(r"[A-Z]", password):
        raise PasswordNotComplexEnoughException(
            "Password must contain at least one uppercase letter."
        )
    if not re_search(r"[a-z]", password):
        raise PasswordNotComplexEnoughException(
            "Password must contain at least one lowercase letter."
        )
    if not re_search(r"[0-9]", password):
        raise PasswordNotComplexEnoughException(
            "Password must contain at least one digit."
        )
    if not re_search(r"[^A-Za-z0-9]", password):
        raise PasswordNotComplexEnoughException(
            "Password must contain at least one special character."
        )


def _hash_password(plain_password: str) -> str:
    return pwd_context.hash(plain_password)
