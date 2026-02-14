from uuid import uuid4

from fastapi import APIRouter

from app.schemas.users import UserCreate, UserOut

router = APIRouter(prefix="/api/v1")


@router.post("/users", response_model=UserOut)
async def create_user(create_data: UserCreate):
    new_user = UserOut(
        id=uuid4(),
        email=create_data.email,
        active=create_data.active,
    )
    return new_user
