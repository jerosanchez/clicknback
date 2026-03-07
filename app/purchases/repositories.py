from abc import ABC, abstractmethod

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.purchases.models import Purchase


class PurchaseRepositoryABC(ABC):
    @abstractmethod
    async def get_by_external_id(
        self, db: AsyncSession, external_id: str
    ) -> Purchase | None:
        pass

    @abstractmethod
    async def add_purchase(self, db: AsyncSession, purchase: Purchase) -> Purchase:
        pass


class PurchaseRepository(PurchaseRepositoryABC):
    async def get_by_external_id(
        self, db: AsyncSession, external_id: str
    ) -> Purchase | None:
        result = await db.execute(
            select(Purchase).where(Purchase.external_id == external_id)
        )
        return result.scalar_one_or_none()

    async def add_purchase(self, db: AsyncSession, purchase: Purchase) -> Purchase:
        db.add(purchase)
        await db.commit()
        await db.refresh(purchase)
        return purchase
