from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr


class UserSchemaBase(BaseModel):
    email: EmailStr
    active: bool = True


class UserOut(UserSchemaBase):
    id: UUID
    role: str = "user"
    created_at: datetime = datetime.now()

    model_config = {"from_attributes": True}


class UserCreate(UserSchemaBase):
    password: str
