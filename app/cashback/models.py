import uuid
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import Enum

from sqlalchemy import ForeignKey, Index, Numeric, String, text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class CashbackTransactionStatus(str, Enum):
    PENDING = "pending"
    AVAILABLE = "available"
    REVERSED = "reversed"


@dataclass
class CashbackResult:
    offer_id: str
    cashback_amount: Decimal
    percentage_applied: float | None
    fixed_amount_applied: float | None


class CashbackTransaction(Base):
    __tablename__ = "cashback_transactions"

    id: Mapped[str] = mapped_column(
        primary_key=True, index=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)
    purchase_id: Mapped[str] = mapped_column(
        ForeignKey("purchases.id"), nullable=False, unique=True
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(precision=12, scale=2))
    status: Mapped[str] = mapped_column(
        String, server_default=text(f"'{CashbackTransactionStatus.PENDING.value}'")
    )
    created_at: Mapped[datetime] = mapped_column(server_default=text("now()"))

    __table_args__ = (
        Index("ix_cashback_transactions_user_id", "user_id"),
        Index("ix_cashback_transactions_status", "status"),
    )
