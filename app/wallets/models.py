from decimal import Decimal

from sqlalchemy import ForeignKey, Numeric, text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Wallet(Base):
    __tablename__ = "wallets"

    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id"), primary_key=True, nullable=False
    )
    pending_balance: Mapped[Decimal] = mapped_column(
        Numeric(precision=12, scale=2), server_default=text("0")
    )
    available_balance: Mapped[Decimal] = mapped_column(
        Numeric(precision=12, scale=2), server_default=text("0")
    )
    paid_balance: Mapped[Decimal] = mapped_column(
        Numeric(precision=12, scale=2), server_default=text("0")
    )
