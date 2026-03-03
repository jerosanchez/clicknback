import uuid
from datetime import date

from sqlalchemy import ForeignKey, Index, text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Offer(Base):
    __tablename__ = "offers"

    id: Mapped[str] = mapped_column(
        primary_key=True, index=True, default=lambda: str(uuid.uuid4())
    )
    merchant_id: Mapped[str] = mapped_column(ForeignKey("merchants.id"), nullable=False)
    percentage: Mapped[float] = mapped_column()
    fixed_amount: Mapped[float | None] = mapped_column(nullable=True)
    start_date: Mapped[date] = mapped_column()
    end_date: Mapped[date] = mapped_column()
    monthly_cap_per_user: Mapped[float] = mapped_column()
    active: Mapped[bool] = mapped_column(server_default=text("true"))

    __table_args__ = (
        Index("ix_offers_merchant_id", "merchant_id"),
        Index("ix_offers_merchant_active", "merchant_id", "active"),
    )
