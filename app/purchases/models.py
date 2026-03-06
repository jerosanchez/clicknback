import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import ForeignKey, Index, Numeric, String, text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Purchase(Base):
    __tablename__ = "purchases"

    id: Mapped[str] = mapped_column(
        primary_key=True, index=True, default=lambda: str(uuid.uuid4())
    )
    external_id: Mapped[str] = mapped_column(String, unique=True, index=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)
    merchant_id: Mapped[str] = mapped_column(ForeignKey("merchants.id"), nullable=False)
    offer_id: Mapped[str | None] = mapped_column(ForeignKey("offers.id"), nullable=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(precision=12, scale=2))
    currency: Mapped[str] = mapped_column(String(3))
    status: Mapped[str] = mapped_column(String, server_default=text("'pending'"))
    created_at: Mapped[datetime] = mapped_column(server_default=text("now()"))

    __table_args__ = (
        Index("ix_purchases_user_id", "user_id"),
        Index("ix_purchases_merchant_id", "merchant_id"),
        Index("ix_purchases_status", "status"),
    )
