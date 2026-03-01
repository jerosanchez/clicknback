from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.errors.builders import (
    business_rule_violation_error,
    internal_server_error,
    validation_error,
)
from app.core.logging import logging
from app.users.composition import get_user_service
from app.users.errors import ErrorCode
from app.users.exceptions import (
    EmailAlreadyRegisteredException,
    PasswordNotComplexEnoughException,
)
from app.users.schemas import UserCreate, UserOut
from app.users.services import (
    UserService,
)

router = APIRouter(prefix="/users")


@router.post("/", response_model=UserOut, status_code=status.HTTP_201_CREATED)
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
    except Exception as e:
        logging.error(
            "An unexpected error occurred during user creation.",
            extra={"error": str(e)},
        )
        raise internal_server_error()

    return new_user
