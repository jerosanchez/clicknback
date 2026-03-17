from abc import ABC, abstractmethod
from decimal import Decimal

from app.cashback.models import CashbackResult


class CashbackCalculatorABC(ABC):
    @abstractmethod
    def calculate(
        self,
        offer_id: str,
        percentage: float,
        fixed_amount: float | None,
        purchase_amount: Decimal,
    ) -> CashbackResult:
        pass


class CashbackCalculator(CashbackCalculatorABC):
    def calculate(
        self,
        offer_id: str,
        percentage: float,
        fixed_amount: float | None,
        purchase_amount: Decimal,
    ) -> CashbackResult:
        if fixed_amount is not None:
            amount = Decimal(str(fixed_amount)).quantize(Decimal("0.01"))
            return CashbackResult(
                offer_id=offer_id,
                cashback_amount=amount,
                percentage_applied=None,
                fixed_amount_applied=fixed_amount,
            )

        amount = (purchase_amount * Decimal(str(percentage)) / Decimal("100")).quantize(
            Decimal("0.01")
        )
        return CashbackResult(
            offer_id=offer_id,
            cashback_amount=amount,
            percentage_applied=percentage,
            fixed_amount_applied=None,
        )
