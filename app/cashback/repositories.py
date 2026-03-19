from abc import ABC, abstractmethod
from decimal import Decimal

from sqlalchemy import update
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
