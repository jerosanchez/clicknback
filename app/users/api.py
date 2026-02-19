from collections.abc import Callable

from fastapi import APIRouter, Depends, status
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.errors.builders import (
    business_rule_violation_error,
    internal_server_error,
    validation_error,
)
from app.users.errors import ErrorCode
from app.users.exceptions import (
    EmailAlreadyRegisteredException,
    PasswordNotComplexEnoughException,
)
from app.users.policies import enforce_password_complexity
from app.users.repositories import UserRepository
from app.users.schemas import UserCreate, UserOut
from app.users.services import (
    UserService,
)

router = APIRouter(prefix="/api/v1")

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


@router.post("/users", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def create_user(
    create_data: UserCreate,
    user_service: UserService = Depends(get_user_service),
    db: Session = Depends(get_db),
) -> UserOut:
    try:
        new_user = user_service.create_user(create_data.model_dump(), db)
    except EmailAlreadyRegisteredException as exc:
        raise business_rule_violation_error(
            ErrorCode.EMAIL_ALREADY_REGISTERED,
            str(exc),
            {"email": exc.email},
        )
    except PasswordNotComplexEnoughException as exc:
        raise validation_error(
            ErrorCode.PASSWORD_NOT_COMPLEX_ENOUGH,
            "Password does not meet complexity requirements.",
            [
                {
                    "field": "password",
                    "reason": exc.reason,
                },
            ],
        )
    except Exception:
        raise internal_server_error()

    return new_user
