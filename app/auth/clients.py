from abc import ABC, abstractmethod
from typing import Optional

from sqlalchemy.orm import Session

from app.auth.models import User
from app.users.repositories import UserRepository


class UserClientABC(ABC):
    @abstractmethod
    def get_user_by_email(self, db: Session, email: str) -> Optional[User]:
        pass


class UserClient(UserClientABC):
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    def get_user_by_email(self, db: Session, email: str) -> Optional[User]:
        user = self.user_repository.get_user_by_email(db, email)
        if user:
            return User(
                id=str(user.id),
                email=str(user.email),
                hashed_password=str(user.hashed_password),
            )
        return None
