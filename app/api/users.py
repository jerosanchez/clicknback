from re import search as re_search
from uuid import uuid4

from fastapi import APIRouter, HTTPException, status
from passlib.context import CryptContext

from app.schemas.users import UserCreate, UserOut


class PasswordNotComplexEnoughException(Exception):
    pass


router = APIRouter(prefix="/api/v1")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


@router.post("/users", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def create_user(create_data: UserCreate):

    # Simulate email uniqueness check, to be implemented with a real database
    if create_data.email == "olduser@example.com":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered.",
        )

    try:
        _check_password_complexity(create_data.password)
    except PasswordNotComplexEnoughException as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        )

    # TODO: to be stored in the database along with the user data
    _hashed_password = _hash_password(create_data.password)

    new_user = UserOut(
        id=uuid4(),
        email=create_data.email,
    )

    return new_user


def _check_password_complexity(password: str) -> None:
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
