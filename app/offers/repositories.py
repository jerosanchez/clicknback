from abc import ABC, abstractmethod
from datetime import date

from sqlalchemy.orm import Session

from app.offers.models import Offer


class OfferRepositoryABC(ABC):
    @abstractmethod
    def add_offer(self, db: Session, offer: Offer) -> Offer:
        pass

    @abstractmethod
    def has_active_offer_for_merchant(self, db: Session, merchant_id: str) -> bool:
        pass

    @abstractmethod
    def list_offers(
        self,
        db: Session,
        page: int,
        page_size: int,
        active: bool | None = None,
        merchant_id: str | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
    ) -> tuple[list[Offer], int]:
        pass


class OfferRepository(OfferRepositoryABC):
    def add_offer(self, db: Session, offer: Offer) -> Offer:
        db.add(offer)
        db.commit()
        db.refresh(offer)
        return offer

    def has_active_offer_for_merchant(self, db: Session, merchant_id: str) -> bool:
        return (
            db.query(Offer)
            .filter(Offer.merchant_id == merchant_id, Offer.active.is_(True))
            .first()
            is not None
        )

    def list_offers(
        self,
        db: Session,
        page: int,
        page_size: int,
        active: bool | None = None,
        merchant_id: str | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
    ) -> tuple[list[Offer], int]:
        query = db.query(Offer)
        if active is not None:
            query = query.filter(Offer.active == active)
        if merchant_id is not None:
            query = query.filter(Offer.merchant_id == merchant_id)

        # Overlap condition: offer validity window intersects [date_from, date_to]
        if date_from is not None:
            query = query.filter(Offer.end_date >= date_from)
        if date_to is not None:
            query = query.filter(Offer.start_date <= date_to)

        total = query.count()
        items = query.offset((page - 1) * page_size).limit(page_size).all()
        return items, total
