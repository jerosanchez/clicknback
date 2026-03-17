from dataclasses import dataclass
from decimal import Decimal


@dataclass
class CashbackResult:
    offer_id: str
    cashback_amount: Decimal
    percentage_applied: float | None
    fixed_amount_applied: float | None
