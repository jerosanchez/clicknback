from abc import ABC, abstractmethod
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.users.repositories import UserRepository


class UsersClientABC(ABC):
    @abstractmethod
    async def get_user_by_email(self, db: AsyncSession, email: str) -> Optional[User]:
        pass


# A modular monolith version of the UsersClient that directly interacts with the UserRepository.
# Should `auth` become a separate microservice, this client can be
# easily replaced with an API client that makes HTTP requests to the `users` service.
class UsersClient(UsersClientABC):
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    async def get_user_by_email(self, db: AsyncSession, email: str) -> Optional[User]:
        user = await self.user_repository.get_user_by_email(db, email)
        if user:
            return User(
                id=str(user.id),
                email=str(user.email),
                hashed_password=str(user.hashed_password),
                role=str(user.role.value),
            )
        return None
