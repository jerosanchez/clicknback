from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.cashback.repositories import CashbackTransactionRepository


@dataclass
class CashbackTransactionDTO:
    id: str
    purchase_id: str
    amount: Decimal
    status: str
    created_at: datetime


class CashbackClientABC(ABC):
    """Read-only interface for cashback transaction data consumed by the wallets module."""

    @abstractmethod
    async def list_by_user_id(
        self, db: AsyncSession, user_id: str, limit: int, offset: int
    ) -> tuple[list[CashbackTransactionDTO], int]:
        """Return a page of cashback transactions for the given user, newest first."""


class CashbackClient(CashbackClientABC):
    """Modular-monolith implementation backed by CashbackTransactionRepository.

    Replace with an HTTP client if the cashback module is ever extracted to a
    separate service; only this class needs to change.
    """

    def __init__(self) -> None:
        self._repository = CashbackTransactionRepository()

    async def list_by_user_id(
        self, db: AsyncSession, user_id: str, limit: int, offset: int
    ) -> tuple[list[CashbackTransactionDTO], int]:
        txns, total = await self._repository.list_by_user_id(db, user_id, limit, offset)
        return (
            [
                CashbackTransactionDTO(
                    id=txn.id,
                    purchase_id=txn.purchase_id,
                    amount=txn.amount,
                    status=txn.status,
                    created_at=txn.created_at,
                )
                for txn in txns
            ],
            total,
        )
