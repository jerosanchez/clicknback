from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.cashback.calculator import CashbackCalculator, CashbackCalculatorABC
from app.cashback.models import CashbackResult, CashbackTransactionStatus
from app.cashback.repositories import CashbackTransactionRepository

# pylint: disable=too-few-public-methods


@dataclass
class CashbackResultDTO:
    offer_id: str
    cashback_amount: Decimal


class CashbackClientABC(ABC):
    """Interface for all cashback operations owned by the cashback module.

    Covers both calculation (pure, sync) and transaction recording (DB, async).

    Transaction contract
    --------------------
    All async methods flush their SQL to the current session but do **not**
    commit. The caller is responsible for committing so cashback writes are
    batched atomically with the originating purchase operation.
    """

    @abstractmethod
    def calculate(
        self,
        offer_id: str,
        percentage: float,
        fixed_amount: float | None,
        purchase_amount: Decimal,
    ) -> CashbackResultDTO:
        """Calculate the cashback amount for a purchase. Pure, no side effects."""

    @abstractmethod
    async def create(
        self, db: AsyncSession, purchase_id: str, user_id: str, amount: Decimal
    ) -> None:
        """Create a new cashback transaction in 'pending' status.

        Flushed but not committed — caller must commit.
        """

    @abstractmethod
    async def confirm(self, db: AsyncSession, purchase_id: str) -> None:
        """Move the cashback transaction for this purchase to 'available'.

        Flushed but not committed — caller must commit.
        """

    @abstractmethod
    async def reverse(self, db: AsyncSession, purchase_id: str) -> None:
        """Move the cashback transaction for this purchase to 'reversed'.

        Valid from both 'pending' (rejection before confirmation) and
        'available' (admin reversal after confirmation) states.
        Flushed but not committed — caller must commit.
        """


class CashbackClient(CashbackClientABC):
    """Modular-monolith implementation.

    Delegates calculation to CashbackCalculator and transaction recording to
    CashbackTransactionRepository. Replace with an HTTP client if the cashback
    module is ever extracted to a separate service; only this class needs to
    change.
    """

    def __init__(self, calculator: CashbackCalculatorABC | None = None) -> None:
        self._calculator: CashbackCalculatorABC = calculator or CashbackCalculator()
        self._repository = CashbackTransactionRepository()

    def calculate(
        self,
        offer_id: str,
        percentage: float,
        fixed_amount: float | None,
        purchase_amount: Decimal,
    ) -> CashbackResultDTO:
        result: CashbackResult = self._calculator.calculate(
            offer_id=offer_id,
            percentage=percentage,
            fixed_amount=fixed_amount,
            purchase_amount=purchase_amount,
        )
        return CashbackResultDTO(
            offer_id=result.offer_id,
            cashback_amount=result.cashback_amount,
        )

    async def create(
        self, db: AsyncSession, purchase_id: str, user_id: str, amount: Decimal
    ) -> None:
        await self._repository.create(db, purchase_id, user_id, amount)

    async def confirm(self, db: AsyncSession, purchase_id: str) -> None:
        await self._repository.update_status(
            db, purchase_id, CashbackTransactionStatus.AVAILABLE.value
        )

    async def reverse(self, db: AsyncSession, purchase_id: str) -> None:
        await self._repository.update_status(
            db, purchase_id, CashbackTransactionStatus.REVERSED.value
        )
