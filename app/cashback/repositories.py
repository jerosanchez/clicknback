from abc import ABC, abstractmethod
from decimal import Decimal

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.cashback.models import CashbackTransaction


class CashbackTransactionRepositoryABC(ABC):
    @abstractmethod
    async def create(
        self, db: AsyncSession, purchase_id: str, user_id: str, amount: Decimal
    ) -> CashbackTransaction:
        """Insert a new pending cashback transaction and flush to the session."""

    @abstractmethod
    async def update_status(
        self, db: AsyncSession, purchase_id: str, status: str
    ) -> None:
        """Update the status of the cashback transaction for the given purchase.

        Flushed but not committed — caller must commit.
        """

    @abstractmethod
    async def list_by_user_id(
        self, db: AsyncSession, user_id: str, limit: int, offset: int
    ) -> tuple[list[CashbackTransaction], int]:
        """Return a page of cashback transactions for *user_id*, newest first."""


class CashbackTransactionRepository(CashbackTransactionRepositoryABC):
    async def create(
        self, db: AsyncSession, purchase_id: str, user_id: str, amount: Decimal
    ) -> CashbackTransaction:
        txn = CashbackTransaction(
            purchase_id=purchase_id,
            user_id=user_id,
            amount=amount,
        )
        db.add(txn)
        await db.flush()
        return txn

    async def update_status(
        self, db: AsyncSession, purchase_id: str, status: str
    ) -> None:
        stmt = (
            update(CashbackTransaction)
            .where(CashbackTransaction.purchase_id == purchase_id)
            .values(status=status)
        )
        await db.execute(stmt)

    async def list_by_user_id(
        self, db: AsyncSession, user_id: str, limit: int, offset: int
    ) -> tuple[list[CashbackTransaction], int]:
        count_stmt = (
            select(func.count())
            .select_from(CashbackTransaction)
            .where(CashbackTransaction.user_id == user_id)
        )
        count_result = await db.execute(count_stmt)
        total: int = count_result.scalar_one()

        items_stmt = (
            select(CashbackTransaction)
            .where(CashbackTransaction.user_id == user_id)
            .order_by(CashbackTransaction.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        items_result = await db.execute(items_stmt)
        items = list(items_result.scalars().all())

        return items, total
