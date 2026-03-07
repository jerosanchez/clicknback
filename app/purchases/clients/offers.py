from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.offers.models import Offer


@dataclass
class OfferDTO:
    id: str
    merchant_id: str
    active: bool
    start_date: date
    end_date: date


class OffersClientABC(ABC):
    @abstractmethod
    async def get_active_offer_for_merchant(
        self, db: AsyncSession, merchant_id: str, today: date
    ) -> OfferDTO | None:
        pass


class OffersClient(OffersClientABC):
    """Modular-monolith implementation — queries the shared DB directly.

    Replace with an HTTP client if the offers module is ever extracted to a
    separate service.
    """

    async def get_active_offer_for_merchant(
        self, db: AsyncSession, merchant_id: str, today: date
    ) -> OfferDTO | None:
        # TODO: This is a temporary implementation that queries the DB directly.
        # When the offers module has async support, this should be replaced with calls to the
        # offers repository, to keep query logic where it belongs.
        result = await db.execute(
            select(Offer).where(
                Offer.merchant_id == merchant_id,
                Offer.active.is_(True),
                Offer.start_date <= today,
                Offer.end_date >= today,
            )
        )
        offer = result.scalar_one_or_none()
        if offer is None:
            return None
        return OfferDTO(
            id=offer.id,
            merchant_id=offer.merchant_id,
            active=offer.active,
            start_date=offer.start_date,
            end_date=offer.end_date,
        )
