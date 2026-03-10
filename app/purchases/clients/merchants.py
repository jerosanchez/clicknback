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


class MerchantsClient(MerchantsClientABC):
    """Modular-monolith implementation — queries the shared DB directly.

    Replace with an HTTP client if the merchants module is ever extracted to a
    separate service.
    """

    async def get_merchant_by_id(
        self, db: AsyncSession, merchant_id: str
    ) -> MerchantDTO | None:
        # TODO: This is a temporary implementation that queries the DB directly.
        # When the merchants module has async support, this should be replaced with calls to the
        # merchants repository, to keep query logic where it belongs.
        result = await db.execute(select(Merchant).where(Merchant.id == merchant_id))
        merchant = result.scalar_one_or_none()
        if merchant is None:
            return None
        return MerchantDTO(id=merchant.id, active=merchant.active, name=merchant.name)
