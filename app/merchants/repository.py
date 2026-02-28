from abc import ABC, abstractmethod

from sqlalchemy.orm import Session

from app.merchants.models import Merchant


class MerchantRepositoryABC(ABC):
    @abstractmethod
    def get_merchant_by_name(self, db: Session, name: str) -> Merchant | None:
        pass

    @abstractmethod
    def get_merchant_by_id(self, db: Session, merchant_id: str) -> Merchant | None:
        pass

    @abstractmethod
    def add_merchant(self, db: Session, merchant: Merchant) -> Merchant:
        pass

    @abstractmethod
    def list_merchants(
        self,
        db: Session,
        page: int,
        page_size: int,
        active: bool | None = None,
    ) -> tuple[list[Merchant], int]:
        pass

    @abstractmethod
    def update_merchant_status(
        self, db: Session, merchant: Merchant, active: bool
    ) -> Merchant:
        pass


class MerchantRepository(MerchantRepositoryABC):
    def get_merchant_by_name(self, db: Session, name: str) -> Merchant | None:
        return db.query(Merchant).filter(Merchant.name == name).first()

    def get_merchant_by_id(self, db: Session, merchant_id: str) -> Merchant | None:
        return db.query(Merchant).filter(Merchant.id == merchant_id).first()

    def add_merchant(self, db: Session, merchant: Merchant) -> Merchant:
        db.add(merchant)
        db.commit()
        db.refresh(merchant)
        return merchant

    def list_merchants(
        self,
        db: Session,
        page: int,
        page_size: int,
        active: bool | None = None,
    ) -> tuple[list[Merchant], int]:
        query = db.query(Merchant)
        if active is not None:
            query = query.filter(Merchant.active == active)
        total = query.count()
        items = query.offset((page - 1) * page_size).limit(page_size).all()
        return items, total

    def update_merchant_status(
        self, db: Session, merchant: Merchant, active: bool
    ) -> Merchant:
        merchant.active = active
        db.commit()
        db.refresh(merchant)
        return merchant
