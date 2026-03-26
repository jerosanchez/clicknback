from abc import ABC, abstractmethod
from decimal import Decimal

from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.wallets.models import Wallet


class WalletRepositoryABC(ABC):
    @abstractmethod
    async def get_by_user_id(self, db: AsyncSession, user_id: str) -> Wallet | None:
        """Return the wallet row for *user_id*, or None if it does not exist yet."""

    @abstractmethod
    async def credit_pending(
        self, db: AsyncSession, user_id: str, amount: Decimal
    ) -> None:
        """Upsert wallet row and add *amount* to pending_balance.

        Creates the wallet row (with zero balances) if it does not exist yet.
        Flushed but not committed — caller must commit so the wallet write can
        be batched atomically with the originating purchase insert.
        """

    @abstractmethod
    async def confirm_pending(
        self, db: AsyncSession, user_id: str, amount: Decimal
    ) -> None:
        """Move *amount* from pending_balance to available_balance.

        Decrements pending_balance and increments available_balance by the same
        amount in a single UPDATE.  Flushed but not committed — caller must
        commit.
        """

    @abstractmethod
    async def reverse_pending(
        self, db: AsyncSession, user_id: str, amount: Decimal
    ) -> None:
        """Remove *amount* from pending_balance (purchase rejected/reversed).

        Decrements pending_balance only.  Flushed but not committed — caller
        must commit.
        """

    @abstractmethod
    async def reverse_available(
        self, db: AsyncSession, user_id: str, amount: Decimal
    ) -> None:
        """Remove *amount* from available_balance (confirmed purchase reversed).

        Decrements available_balance only.  Flushed but not committed — caller
        must commit.
        """


class WalletRepository(WalletRepositoryABC):
    async def get_by_user_id(self, db: AsyncSession, user_id: str) -> Wallet | None:
        """Return the wallet row for *user_id*, or None if it does not exist yet."""
        result = await db.execute(select(Wallet).where(Wallet.user_id == user_id))
        return result.scalar_one_or_none()

    async def credit_pending(
        self, db: AsyncSession, user_id: str, amount: Decimal
    ) -> None:
        """Upsert wallet row and atomically add *amount* to pending_balance."""
        stmt = (
            insert(Wallet)
            .values(
                user_id=user_id,
                pending_balance=amount,
                available_balance=Decimal("0"),
                paid_balance=Decimal("0"),
            )
            .on_conflict_do_update(
                index_elements=["user_id"],
                set_={
                    "pending_balance": Wallet.pending_balance + amount,
                },
            )
        )
        await db.execute(stmt)

    async def confirm_pending(
        self, db: AsyncSession, user_id: str, amount: Decimal
    ) -> None:
        """Move *amount* from pending_balance to available_balance."""
        stmt = (
            update(Wallet)
            .where(Wallet.user_id == user_id)
            .values(
                pending_balance=Wallet.pending_balance - amount,
                available_balance=Wallet.available_balance + amount,
            )
        )
        await db.execute(stmt)

    async def reverse_pending(
        self, db: AsyncSession, user_id: str, amount: Decimal
    ) -> None:
        """Remove *amount* from pending_balance."""
        stmt = (
            update(Wallet)
            .where(Wallet.user_id == user_id)
            .values(pending_balance=Wallet.pending_balance - amount)
        )
        await db.execute(stmt)

    async def reverse_available(
        self, db: AsyncSession, user_id: str, amount: Decimal
    ) -> None:
        """Remove *amount* from available_balance."""
        stmt = (
            update(Wallet)
            .where(Wallet.user_id == user_id)
            .values(available_balance=Wallet.available_balance - amount)
        )
        await db.execute(stmt)
