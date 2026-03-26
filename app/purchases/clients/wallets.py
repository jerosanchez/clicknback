from abc import ABC, abstractmethod
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.wallets.repositories import WalletRepository


class WalletsClientABC(ABC):
    """Interface for wallet balance operations owned by the wallets module.

    Transaction contract
    --------------------
    All methods flush their SQL to the current session but do **not** commit.
    The caller is responsible for committing so the wallet write can be batched
    atomically with the originating purchase operation (insert or status update)
    in a single DB transaction.
    """

    @abstractmethod
    async def credit_pending(
        self, db: AsyncSession, user_id: str, amount: Decimal
    ) -> None:
        """Add *amount* to the user's pending_balance.

        Creates the wallet row with zero balances if it does not exist yet.
        Flushed but not committed — caller must commit.
        """

    @abstractmethod
    async def confirm_pending(
        self, db: AsyncSession, user_id: str, amount: Decimal
    ) -> None:
        """Move *amount* from pending_balance to available_balance.

        Flushed but not committed — caller must commit.
        """

    @abstractmethod
    async def reverse_pending(
        self, db: AsyncSession, user_id: str, amount: Decimal
    ) -> None:
        """Remove *amount* from pending_balance (purchase rejected/reversed).

        Flushed but not committed — caller must commit.
        """

    @abstractmethod
    async def reverse_available(
        self, db: AsyncSession, user_id: str, amount: Decimal
    ) -> None:
        """Remove *amount* from available_balance (confirmed purchase reversed).

        Flushed but not committed — caller must commit.
        """


class WalletsClient(WalletsClientABC):
    """Modular-monolith implementation — delegates to ``WalletRepository``."""

    def __init__(self) -> None:
        self._repository = WalletRepository()

    async def credit_pending(
        self, db: AsyncSession, user_id: str, amount: Decimal
    ) -> None:
        await self._repository.credit_pending(db, user_id, amount)

    async def confirm_pending(
        self, db: AsyncSession, user_id: str, amount: Decimal
    ) -> None:
        await self._repository.confirm_pending(db, user_id, amount)

    async def reverse_pending(
        self, db: AsyncSession, user_id: str, amount: Decimal
    ) -> None:
        await self._repository.reverse_pending(db, user_id, amount)

    async def reverse_available(
        self, db: AsyncSession, user_id: str, amount: Decimal
    ) -> None:
        await self._repository.reverse_available(db, user_id, amount)
