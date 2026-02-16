import enum
import uuid

from sqlalchemy import Boolean, Column, Enum, Index, String
from sqlalchemy.sql.sqltypes import TIMESTAMP

from app.core.database import Base


class UserRoleEnum(str, enum.Enum):
    user = "user"
    admin = "admin"


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, nullable=False, unique=True)
    hashed_password = Column(String, nullable=False)
    role = Column(Enum(UserRoleEnum), nullable=False, default=UserRoleEnum.user)
    active = Column(Boolean, server_default="TRUE", nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default="now()")

    __table_args__ = (Index("users_email_key", "email", unique=True),)
