from typing import Any, Callable

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import logger
from app.core.unit_of_work import UnitOfWorkABC
from app.users.exceptions import EmailAlreadyRegisteredException
from app.users.models import User
from app.users.repositories import UserRepositoryABC


class UserService:
    def __init__(
        self,
        enforce_password_complexity: Callable[[str], None],
        hash_password: Callable[[str], str],
        user_repository: UserRepositoryABC,
    ):
        self.enforce_password_complexity = enforce_password_complexity
        self.hash_password = hash_password
        self.user_repository = user_repository

    async def create_user(
        self, create_data: dict[str, Any], uow: UnitOfWorkABC
    ) -> User:
        email = create_data["email"]
        password = create_data["password"]

        self.enforce_password_complexity(password)

        await self._enforce_email_uniqueness(email, uow.session)

        hashed_password = self.hash_password(password)
        new_user = User(email=email, hashed_password=hashed_password, active=True)

        result = await self.user_repository.add_user(uow.session, new_user)
        await uow.commit()
        return result

    async def _enforce_email_uniqueness(self, email: str, db: AsyncSession) -> None:
        if await self.user_repository.get_user_by_email(db, email):
            logger.info(
                "Attempt to register a user with an existing email.",
                extra={"email": email},
            )
            raise EmailAlreadyRegisteredException(email)
