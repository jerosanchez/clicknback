from abc import ABC, abstractmethod

from sqlalchemy.orm import Session

from app.merchants.models import Merchant


class MerchantRepositoryABC(ABC):
    @abstractmethod
    def get_merchant_by_name(self, db: Session, name: str) -> Merchant | None:
        pass

    @abstractmethod
    def add_merchant(self, db: Session, merchant: Merchant) -> Merchant:
        pass


class MerchantRepository(MerchantRepositoryABC):
    def get_merchant_by_name(self, db: Session, name: str) -> Merchant | None:
        return db.query(Merchant).filter(Merchant.name == name).first()

    def add_merchant(self, db: Session, merchant: Merchant) -> Merchant:
        db.add(merchant)
        db.commit()
        db.refresh(merchant)
        return merchant
