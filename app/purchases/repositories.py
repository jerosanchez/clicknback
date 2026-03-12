from abc import ABC, abstractmethod
from datetime import date, timedelta

from sqlalchemy import ColumnElement, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.purchases.models import Purchase


class PurchaseRepositoryABC(ABC):
    @abstractmethod
    async def get_by_external_id(
        self, db: AsyncSession, external_id: str
    ) -> Purchase | None:
        pass

    @abstractmethod
    async def get_by_id(self, db: AsyncSession, purchase_id: str) -> Purchase | None:
        pass

    @abstractmethod
    async def add_purchase(self, db: AsyncSession, purchase: Purchase) -> Purchase:
        pass

    @abstractmethod
    async def get_pending_purchases(self, db: AsyncSession) -> list[Purchase]:
        """Return all purchases with status 'pending', ordered by creation date."""

    @abstractmethod
    async def update_status(
        self, db: AsyncSession, purchase_id: str, new_status: str
    ) -> Purchase | None:
        """Update the status of a purchase and return the updated record."""

    @abstractmethod
    async def list_purchases(
        self,
        db: AsyncSession,
        *,
        status: str | None = None,
        user_id: str | None = None,
        merchant_id: str | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
        page: int = 1,
        page_size: int = settings.default_page_size,
    ) -> tuple[list[Purchase], int]:
        pass


class PurchaseRepository(PurchaseRepositoryABC):
    async def get_by_external_id(
        self, db: AsyncSession, external_id: str
    ) -> Purchase | None:
        result = await db.execute(
            select(Purchase).where(Purchase.external_id == external_id)
        )
        return result.scalar_one_or_none()

    async def get_by_id(self, db: AsyncSession, purchase_id: str) -> Purchase | None:
        result = await db.execute(select(Purchase).where(Purchase.id == purchase_id))
        return result.scalar_one_or_none()

    async def add_purchase(self, db: AsyncSession, purchase: Purchase) -> Purchase:
        db.add(purchase)
        await db.commit()
        await db.refresh(purchase)
        return purchase

    async def get_pending_purchases(self, db: AsyncSession) -> list[Purchase]:
        result = await db.execute(
            select(Purchase)
            .where(Purchase.status == "pending")
            .order_by(Purchase.created_at)
        )
        return list(result.scalars().all())

    async def update_status(
        self, db: AsyncSession, purchase_id: str, new_status: str
    ) -> Purchase | None:
        result = await db.execute(select(Purchase).where(Purchase.id == purchase_id))
        purchase = result.scalar_one_or_none()
        if purchase is None:
            return None
        purchase.status = new_status
        await db.commit()
        await db.refresh(purchase)
        return purchase

    async def list_purchases(
        self,
        db: AsyncSession,
        *,
        status: str | None = None,
        user_id: str | None = None,
        merchant_id: str | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
        page: int = 1,
        page_size: int = settings.default_page_size,
    ) -> tuple[list[Purchase], int]:
        conditions = self._build_conditions(
            status=status,
            user_id=user_id,
            merchant_id=merchant_id,
            start_date=start_date,
            end_date=end_date,
        )
        count_stmt = select(func.count(Purchase.id))
        items_stmt = select(Purchase)
        if conditions:
            count_stmt = count_stmt.where(*conditions)
            items_stmt = items_stmt.where(*conditions)

        total: int = (await db.execute(count_stmt)).scalar_one()

        items_stmt = (
            items_stmt.order_by(Purchase.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        result = await db.execute(items_stmt)
        return list(result.scalars().all()), total

    def _build_conditions(
        self,
        *,
        status: str | None = None,
        user_id: str | None = None,
        merchant_id: str | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> list[ColumnElement[bool]]:
        conditions: list[ColumnElement[bool]] = []
        if status is not None:
            conditions.append(Purchase.status == status)
        if user_id is not None:
            conditions.append(Purchase.user_id == user_id)
        if merchant_id is not None:
            conditions.append(Purchase.merchant_id == merchant_id)
        if start_date is not None:
            conditions.append(Purchase.created_at >= start_date)
        if end_date is not None:
            # end_date is inclusive: include all purchases up to end of that day
            conditions.append(Purchase.created_at < end_date + timedelta(days=1))
        return conditions
