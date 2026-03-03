from abc import ABC, abstractmethod

from sqlalchemy.orm import Session

from app.offers.models import Offer


class OfferRepositoryABC(ABC):
    @abstractmethod
    def add_offer(self, db: Session, offer: Offer) -> Offer:
        pass

    @abstractmethod
    def has_active_offer_for_merchant(self, db: Session, merchant_id: str) -> bool:
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
