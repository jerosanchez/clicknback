from abc import ABC, abstractmethod
from datetime import date

from sqlalchemy.orm import Query, Session

from app.offers.models import Offer

# Imported lazily inside methods to avoid circular imports at module load time;
# declared here for annotation purposes only.
_MerchantName = str


class OfferRepositoryABC(ABC):
    @abstractmethod
    def add_offer(self, db: Session, offer: Offer) -> Offer:
        pass

    @abstractmethod
    def get_offer_by_id(self, db: Session, offer_id: str) -> Offer | None:
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

    @abstractmethod
    def list_active_offers(
        self,
        db: Session,
        page: int,
        page_size: int,
        today: date,
    ) -> tuple[list[tuple[Offer, str]], int]:
        pass

    @abstractmethod
    def update_offer_status(self, db: Session, offer: Offer, active: bool) -> Offer:
        pass


class OfferRepository(OfferRepositoryABC):
    def add_offer(self, db: Session, offer: Offer) -> Offer:
        db.add(offer)
        db.commit()
        db.refresh(offer)
        return offer

    def get_offer_by_id(self, db: Session, offer_id: str) -> Offer | None:
        return db.query(Offer).filter(Offer.id == offer_id).first()

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
        query: Query[Offer] = db.query(Offer)
        if active is not None:
            query = query.filter(Offer.active == active)
        if merchant_id is not None:
            query = query.filter(Offer.merchant_id == merchant_id)

        # Overlap condition: offer validity window intersects [date_from, date_to]
        # Technically, to apply an overlap date range strategy is business logic and
        # should be in the service layer, but for simplicity we put it here (for now)
        if date_from is not None:
            query = query.filter(Offer.end_date >= date_from)
        if date_to is not None:
            query = query.filter(Offer.start_date <= date_to)

        total = query.count()
        items = query.offset((page - 1) * page_size).limit(page_size).all()
        return items, total

    def list_active_offers(
        self,
        db: Session,
        page: int,
        page_size: int,
        today: date,
    ) -> tuple[list[tuple[Offer, str]], int]:
        from app.merchants.models import Merchant  # local import to avoid circular deps

        # We are coupling to the Merchants module by using the Merchant model and joining on it here.
        # Besides, we are facing a potential circular import issue since the Offers module might be imported
        # by Merchants module (e.g. to check for active offers for a merchant).
        # TODO: Eventually we might want Offers and Merchants to be separate services,
        # so we should ideally not have direct imports or DB joins between them.
        # For now, we will keep it simple and just be mindful of the coupling and circular import issues.

        query = (
            db.query(Offer, Merchant.name)
            .join(Merchant, Offer.merchant_id == Merchant.id)
            .filter(
                Offer.active.is_(True),
                Merchant.active.is_(True),
                Offer.start_date <= today,
                Offer.end_date >= today,
            )
        )
        total = query.count()
        rows = query.offset((page - 1) * page_size).limit(page_size).all()
        return [(offer, name) for offer, name in rows], total

    def update_offer_status(self, db: Session, offer: Offer, active: bool) -> Offer:
        offer.active = active
        db.commit()
        db.refresh(offer)
        return offer
