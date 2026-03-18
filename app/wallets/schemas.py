from decimal import Decimal

from pydantic import BaseModel


class WalletSummaryOut(BaseModel):
    pending_balance: Decimal
    available_balance: Decimal
    paid_balance: Decimal

    model_config = {"from_attributes": True}
