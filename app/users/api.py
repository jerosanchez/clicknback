from collections.abc import Callable
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.users.exceptions import (
    EmailAlreadyRegisteredException,
    PasswordNotComplexEnoughException,
)
from app.users.password_utils import hash_password
from app.users.policies import enforce_password_complexity
from app.users.repositories import UserRepository
from app.users.schemas import UserCreate, UserOut
from app.users.services import (
    UserService,
)

router = APIRouter(prefix="/api/v1")


def get_enforce_password_complexity() -> Callable[[str], None]:
    return lambda password: enforce_password_complexity(password)


def get_password_hasher():
    return hash_password


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
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": {
                    "code": "EMAIL_ALREADY_REGISTERED",
                    "message": str(exc),
                    "details": {
                        "email": create_data.email,
                    },
                }
            },
        )
    except PasswordNotComplexEnoughException as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {
                    "code": "PASSWORD_NOT_COMPLEX_ENOUGH",
                    "message": "Validation failed for request body.",
                    "details": {
                        "violations": [
                            {
                                "field": "password",
                                "reason": str(exc),
                            },
                        ]
                    },
                }
            },
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {
                    "code": "INTERNAL_SERVER_ERROR",
                    "message": "An unexpected error occurred. Our team has been notified. Please retry later.",
                    "details": {
                        "request_id": "not available",
                        "timestamp": datetime.now().isoformat(),
                    },
                }
            },
        )

    return new_user
