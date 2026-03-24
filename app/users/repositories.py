from abc import ABC, abstractmethod

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import User


class UserRepositoryABC(ABC):
    @abstractmethod
    async def get_user_by_email(self, db: AsyncSession, email: str) -> User | None:
        pass

    @abstractmethod
    async def get_user_by_id(self, db: AsyncSession, user_id: str) -> User | None:
        pass

    @abstractmethod
    async def add_user(self, db: AsyncSession, user: User) -> User:
        pass


class UserRepository(UserRepositoryABC):
    async def get_user_by_email(self, db: AsyncSession, email: str) -> User | None:
        result = await db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def get_user_by_id(self, db: AsyncSession, user_id: str) -> User | None:
        result = await db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def add_user(self, db: AsyncSession, user: User) -> User:
        db.add(user)
        await db.flush()
        await db.refresh(user)
        return user
