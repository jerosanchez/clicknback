from abc import ABC, abstractmethod

from sqlalchemy.orm import Session


class AuthRepositoryABC(ABC):
    @abstractmethod
    def authenticate_user(self, db: Session, email: str, password: str):
        pass


class AuthRepository(AuthRepositoryABC):
    def authenticate_user(self, db: Session, email: str, password: str):
        # Logic to be implemented
        pass
