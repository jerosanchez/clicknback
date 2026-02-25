from abc import ABC, abstractmethod

from sqlalchemy.orm import Session

from app.merchants.models import Merchant


class MerchantRepositoryABC(ABC):
    @abstractmethod
    def add_merchant(self, db: Session, merchant: Merchant) -> Merchant:
        pass


class MerchantRepository(MerchantRepositoryABC):
    def add_merchant(self, db: Session, merchant: Merchant) -> Merchant:
        return merchant
