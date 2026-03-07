from abc import ABC, abstractmethod
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.users.models import User


@dataclass
class UserDTO:
    id: str
    active: bool


class UsersClientABC(ABC):
    @abstractmethod
    async def get_user_by_id(self, db: AsyncSession, user_id: str) -> UserDTO | None:
        pass


class UsersClient(UsersClientABC):
    """Modular-monolith implementation — queries the shared DB directly.

    Replace with an HTTP client if the users module is ever extracted to a
    separate service.
    """

    async def get_user_by_id(self, db: AsyncSession, user_id: str) -> UserDTO | None:
        # TODO: This is a temporary implementation that queries the DB directly.
        # When the users module has async support, this should be replaced with calls to the
        # users repository, to keep query logic where it belongs.
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if user is None:
            return None
        return UserDTO(id=user.id, active=user.active)
