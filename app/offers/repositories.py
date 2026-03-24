from abc import ABC, abstractmethod
from datetime import date

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.offers.models import Offer

# We are coupling to the Merchants module by using the Merchant model and joining on it here.
# Besides, we are facing a potential circular import issue since the Offers module might be imported
# by Merchants module (e.g. to check for active offers for a merchant).

# Imported lazily inside methods to avoid circular imports at module load time;
# declared here for documentation purposes only.
_MerchantName = str

# TODO: Eventually we might want Offers and Merchants to be separate services, so we should ideally
# not have direct imports or DB joins between their corresponding DB tables.
# We can implement a client-service pattern or use domain events for cross-module interactions
# if we decide to split them in the future (with performance considerations).
# For now, we will keep it simple and just be mindful of the coupling and circular import issues.


class OfferRepositoryABC(ABC):
    @abstractmethod
    async def add_offer(self, db: AsyncSession, offer: Offer) -> Offer:
        pass

    @abstractmethod
    async def get_offer_by_id(self, db: AsyncSession, offer_id: str) -> Offer | None:
        pass

    @abstractmethod
    async def has_active_offer_for_merchant(
        self, db: AsyncSession, merchant_id: str
    ) -> bool:
        pass

    @abstractmethod
    async def list_offers(
        self,
        db: AsyncSession,
        page: int,
        page_size: int,
        active: bool | None = None,
        merchant_id: str | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
    ) -> tuple[list[Offer], int]:
        pass

    @abstractmethod
    async def list_active_offers(
        self,
        db: AsyncSession,
        page: int,
        page_size: int,
        today: date,
    ) -> tuple[list[tuple[Offer, str]], int]:
        pass

    @abstractmethod
    async def get_offer_with_merchant_name(
        self, db: AsyncSession, offer_id: str
    ) -> tuple[Offer, str, bool] | None:
        pass

    @abstractmethod
    async def update_offer_status(
        self, db: AsyncSession, offer: Offer, active: bool
    ) -> Offer:
        pass


class OfferRepository(OfferRepositoryABC):
    async def add_offer(self, db: AsyncSession, offer: Offer) -> Offer:
        db.add(offer)
        await db.flush()
        await db.refresh(offer)
        return offer

    async def get_offer_by_id(self, db: AsyncSession, offer_id: str) -> Offer | None:
        result = await db.execute(select(Offer).where(Offer.id == offer_id))
        return result.scalar_one_or_none()

    async def has_active_offer_for_merchant(
        self, db: AsyncSession, merchant_id: str
    ) -> bool:
        stmt = (
            select(Offer.id)
            .where(Offer.merchant_id == merchant_id, Offer.active.is_(True))
            .limit(1)
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def list_offers(
        self,
        db: AsyncSession,
        page: int,
        page_size: int,
        active: bool | None = None,
        merchant_id: str | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
    ) -> tuple[list[Offer], int]:
        stmt = select(Offer)
        if active is not None:
            stmt = stmt.where(Offer.active == active)
        if merchant_id is not None:
            stmt = stmt.where(Offer.merchant_id == merchant_id)

        # Overlap condition: offer validity window intersects [date_from, date_to]
        # Technically, to apply an overlap date range strategy is business logic and
        # should be in the service layer, but for simplicity we put it here (for now)
        if date_from is not None:
            stmt = stmt.where(Offer.end_date >= date_from)
        if date_to is not None:
            stmt = stmt.where(Offer.start_date <= date_to)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await db.execute(count_stmt)).scalar_one()

        items_stmt = stmt.offset((page - 1) * page_size).limit(page_size)
        result = await db.execute(items_stmt)
        items = list(result.scalars().all())
        return items, total

    async def list_active_offers(
        self,
        db: AsyncSession,
        page: int,
        page_size: int,
        today: date,
    ) -> tuple[list[tuple[Offer, str]], int]:
        from app.merchants.models import (
            Merchant,  # local import to avoid potential circular deps
        )

        # IMPORTANT: See note on coupling and circular import issues at the top of the file.

        base_stmt = (
            select(Offer, Merchant.name)
            .join(Merchant, Offer.merchant_id == Merchant.id)
            .where(
                Offer.active.is_(True),
                Merchant.active.is_(True),
                Offer.start_date <= today,
                Offer.end_date >= today,
            )
        )
        count_stmt = select(func.count()).select_from(
            select(Offer.id)
            .join(Merchant, Offer.merchant_id == Merchant.id)
            .where(
                Offer.active.is_(True),
                Merchant.active.is_(True),
                Offer.start_date <= today,
                Offer.end_date >= today,
            )
            .subquery()
        )
        total = (await db.execute(count_stmt)).scalar_one()
        rows = (
            await db.execute(base_stmt.offset((page - 1) * page_size).limit(page_size))
        ).all()
        return [(row[0], row[1]) for row in rows], total

    async def get_offer_with_merchant_name(
        self, db: AsyncSession, offer_id: str
    ) -> tuple[Offer, str, bool] | None:
        from app.merchants.models import (
            Merchant,  # local import to avoid potential circular deps
        )

        # IMPORTANT: See note on coupling and circular import issues at the top of the file.

        stmt = (
            select(Offer, Merchant.name, Merchant.active)
            .join(Merchant, Offer.merchant_id == Merchant.id)
            .where(Offer.id == offer_id)
        )
        row = (await db.execute(stmt)).first()
        if row is None:
            return None
        offer, merchant_name, merchant_active = row
        return offer, merchant_name, merchant_active

    async def update_offer_status(
        self, db: AsyncSession, offer: Offer, active: bool
    ) -> Offer:
        offer.active = active
        await db.flush()
        await db.refresh(offer)
        return offer
