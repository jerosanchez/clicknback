from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.exceptions.users import (
    EmailAlreadyRegisteredException,
    PasswordNotComplexEnoughException,
)
from app.schemas.users import UserCreate, UserOut
from app.services.users import (
    UserService,
)

router = APIRouter(prefix="/api/v1")


def get_user_service():
    return UserService()


@router.post("/users", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def create_user(
    create_data: UserCreate, user_service: UserService = Depends(get_user_service)
):
    try:
        user_service.create_user(create_data)
    except EmailAlreadyRegisteredException as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    except PasswordNotComplexEnoughException as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)
        )

    new_user = UserOut(
        id=uuid4(),
        email=create_data.email,
    )

    return new_user
