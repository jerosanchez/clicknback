from abc import ABC, abstractmethod

from sqlalchemy.orm import Session

from .models import User


class UserRepositoryABC(ABC):
    @abstractmethod
    def get_user_by_email(self, db: Session, email: str) -> User | None:
        pass

    @abstractmethod
    def get_user_by_id(self, db: Session, user_id: str) -> User | None:
        pass

    @abstractmethod
    def add_user(self, db: Session, user: User) -> User:
        pass


class UserRepository(UserRepositoryABC):
    def get_user_by_email(self, db: Session, email: str) -> User | None:
        return db.query(User).filter(User.email == email).first()

    def get_user_by_id(self, db: Session, user_id: str) -> User | None:
        return db.query(User).filter(User.id == user_id).first()

    def add_user(self, db: Session, user: User) -> User:
        db.add(user)
        db.commit()
        db.refresh(user)

        return user
