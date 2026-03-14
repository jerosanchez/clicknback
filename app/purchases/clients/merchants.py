from abc import ABC, abstractmethod
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.merchants.models import Merchant


@dataclass
class MerchantDTO:
    id: str
    active: bool
    name: str


class MerchantsClientABC(ABC):
    @abstractmethod
    async def get_merchant_by_id(
        self, db: AsyncSession, merchant_id: str
    ) -> MerchantDTO | None:
        pass

    @abstractmethod
    async def get_merchants_by_ids(
        self, db: AsyncSession, merchant_ids: list[str]
    ) -> dict[str, MerchantDTO]:
        """Batch-load merchants by ID. Returns a mapping of merchant ID → MerchantDTO."""


class MerchantsClient(MerchantsClientABC):
    """Modular-monolith implementation — queries the shared DB directly.

    Replace with an HTTP client if the merchants module is ever extracted to a
    separate service.
    """

    # TODO: This is a temporary implementation that queries the DB directly.
    # When the merchants module has async support, this should be replaced with calls to the
    # merchants repository to keep query logic where it belongs.

    async def get_merchant_by_id(
        self, db: AsyncSession, merchant_id: str
    ) -> MerchantDTO | None:
        result = await db.execute(select(Merchant).where(Merchant.id == merchant_id))
        merchant = result.scalar_one_or_none()
        if merchant is None:
            return None
        return MerchantDTO(id=merchant.id, active=merchant.active, name=merchant.name)

    async def get_merchants_by_ids(
        self, db: AsyncSession, merchant_ids: list[str]
    ) -> dict[str, MerchantDTO]:
        if not merchant_ids:
            return {}

        result = await db.execute(select(Merchant).where(Merchant.id.in_(merchant_ids)))
        merchants = {m.id: m for m in result.scalars().all()}

        return {
            merchant_id: MerchantDTO(id=m.id, active=m.active, name=m.name)
            for merchant_id, m in merchants.items()
        }
