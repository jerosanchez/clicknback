from dataclasses import dataclass
from datetime import datetime
from uuid import uuid4

from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


# In-memory dataclasses
@dataclass(frozen=True)
class User:
    id: str
    email: str
    hashed_password: str
    role: str


@dataclass(frozen=True)
class Token:
    access_token: str
    token_type: str


@dataclass(frozen=True)
class TokenResponse:
    access_token: str
    refresh_token: str
    token_type: str


@dataclass(frozen=True)
class TokenPayload:
    user_id: str | None = None
    user_role: str | None = None


# ORM Models
class RefreshToken(Base):
    """Stores refresh tokens with metadata for single-use token rotation."""

    __tablename__ = "refresh_tokens"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    user_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    token_hash: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    issued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    used_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    rotation_count: Mapped[int] = mapped_column(default=0, nullable=False)

    def is_expired(self, now: datetime) -> bool:
        """Check if token has expired."""
        return now >= self.expires_at

    def is_used(self) -> bool:
        """Check if token has already been used."""
        return self.used_at is not None
