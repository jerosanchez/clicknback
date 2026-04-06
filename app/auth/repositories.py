"""Repository for managing refresh tokens."""

from abc import ABC, abstractmethod
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import RefreshToken


class RefreshTokenRepositoryABC(ABC):
    """Abstract interface for refresh token persistence."""

    @abstractmethod
    async def create(
        self,
        db: AsyncSession,
        user_id: str,
        token_hash: str,
        issued_at: datetime,
        expires_at: datetime,
    ) -> RefreshToken:
        """Create and store a new refresh token."""
        pass

    @abstractmethod
    async def get_by_hash(
        self, db: AsyncSession, token_hash: str
    ) -> RefreshToken | None:
        """Retrieve a refresh token by its hash."""
        pass

    @abstractmethod
    async def mark_as_used(
        self, db: AsyncSession, token_id: str, used_at: datetime
    ) -> None:
        """Mark a token as used (enforce single-use)."""
        pass


class RefreshTokenRepository(RefreshTokenRepositoryABC):
    """Concrete implementation for refresh token persistence."""

    async def create(
        self,
        db: AsyncSession,
        user_id: str,
        token_hash: str,
        issued_at: datetime,
        expires_at: datetime,
    ) -> RefreshToken:
        """Create and store a new refresh token."""
        token = RefreshToken(
            user_id=user_id,
            token_hash=token_hash,
            issued_at=issued_at,
            expires_at=expires_at,
            rotation_count=0,
        )
        db.add(token)
        await db.flush()
        return token

    async def get_by_hash(
        self, db: AsyncSession, token_hash: str
    ) -> RefreshToken | None:
        """Retrieve a refresh token by its hash."""
        query = select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def mark_as_used(
        self, db: AsyncSession, token_id: str, used_at: datetime
    ) -> None:
        """Mark a token as used and increment rotation count."""
        query = select(RefreshToken).where(RefreshToken.id == token_id)
        result = await db.execute(query)
        token = result.scalar_one_or_none()
        if token:
            token.used_at = used_at
            token.rotation_count += 1
            await db.flush()
