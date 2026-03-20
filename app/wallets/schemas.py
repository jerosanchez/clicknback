from decimal import Decimal
from enum import Enum

from pydantic import BaseModel


class WalletSummaryOut(BaseModel):
    pending_balance: Decimal
    available_balance: Decimal
    paid_balance: Decimal

    model_config = {"from_attributes": True}


class WalletTransactionType(str, Enum):
    CASHBACK_CREDIT = "cashback_credit"


class WalletTransactionOut(BaseModel):
    id: str
    type: WalletTransactionType
    amount: Decimal
    status: str
    related_purchase_id: str | None = None

    model_config = {"from_attributes": True}


class PaginatedWalletTransactionOut(BaseModel):
    transactions: list[WalletTransactionOut]
    total: int
