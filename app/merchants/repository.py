from abc import ABC, abstractmethod

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.merchants.models import Merchant


class MerchantRepositoryABC(ABC):
    @abstractmethod
    async def get_merchant_by_name(
        self, db: AsyncSession, name: str
    ) -> Merchant | None:
        pass

    @abstractmethod
    async def get_merchant_by_id(
        self, db: AsyncSession, merchant_id: str
    ) -> Merchant | None:
        pass

    @abstractmethod
    async def add_merchant(self, db: AsyncSession, merchant: Merchant) -> Merchant:
        pass

    @abstractmethod
    async def list_merchants(
        self,
        db: AsyncSession,
        offset: int,
        limit: int,
        active: bool | None = None,
    ) -> tuple[list[Merchant], int]:
        pass

    @abstractmethod
    async def update_merchant_status(
        self, db: AsyncSession, merchant: Merchant, active: bool
    ) -> Merchant:
        pass


class MerchantRepository(MerchantRepositoryABC):
    async def get_merchant_by_name(
        self, db: AsyncSession, name: str
    ) -> Merchant | None:
        result = await db.execute(select(Merchant).where(Merchant.name == name))
        return result.scalar_one_or_none()

    async def get_merchant_by_id(
        self, db: AsyncSession, merchant_id: str
    ) -> Merchant | None:
        result = await db.execute(select(Merchant).where(Merchant.id == merchant_id))
        return result.scalar_one_or_none()

    async def add_merchant(self, db: AsyncSession, merchant: Merchant) -> Merchant:
        db.add(merchant)
        await db.flush()
        await db.refresh(merchant)
        return merchant

    async def list_merchants(
        self,
        db: AsyncSession,
        offset: int,
        limit: int,
        active: bool | None = None,
    ) -> tuple[list[Merchant], int]:
        stmt = select(Merchant)
        if active is not None:
            stmt = stmt.where(Merchant.active == active)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await db.execute(count_stmt)).scalar_one()

        items_stmt = stmt.offset(offset).limit(limit)
        result = await db.execute(items_stmt)
        items = list(result.scalars().all())
        return items, total

    async def update_merchant_status(
        self, db: AsyncSession, merchant: Merchant, active: bool
    ) -> Merchant:
        merchant.active = active
        await db.flush()
        await db.refresh(merchant)
        return merchant
