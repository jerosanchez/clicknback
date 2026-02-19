from collections.abc import Callable

from passlib.context import CryptContext

from app.users.policies import enforce_password_complexity
from app.users.repositories import UserRepository
from app.users.services import UserService

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_enforce_password_complexity() -> Callable[[str], None]:
    return lambda password: enforce_password_complexity(password)


def get_password_hasher() -> Callable[[str], str]:
    return pwd_context.hash


def get_user_repository():
    return UserRepository()


def get_user_service():
    return UserService(
        get_enforce_password_complexity(),
        get_password_hasher(),
        get_user_repository(),
    )
