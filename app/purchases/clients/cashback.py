from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal

from app.cashback.calculator import CashbackCalculator, CashbackCalculatorABC
from app.cashback.models import CashbackResult

# pylint: disable=too-few-public-methods


@dataclass
class CashbackResultDTO:
    offer_id: str
    cashback_amount: Decimal


class CashbackClientABC(ABC):
    @abstractmethod
    def calculate(
        self,
        offer_id: str,
        percentage: float,
        fixed_amount: float | None,
        purchase_amount: Decimal,
    ) -> CashbackResultDTO:
        pass


class CashbackClient(CashbackClientABC):
    """Modular-monolith implementation — delegates to the cashback calculator.

    Replace with an HTTP client if the cashback module is ever extracted to a
    separate service; only this class needs to change.
    """

    def __init__(self, calculator: CashbackCalculatorABC | None = None) -> None:
        self._calculator: CashbackCalculatorABC = calculator or CashbackCalculator()

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
