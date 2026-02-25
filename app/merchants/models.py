import uuid

from sqlalchemy import text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Merchant(Base):
    __tablename__ = "merchants"

    id: Mapped[str] = mapped_column(
        primary_key=True, index=True, default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str] = mapped_column()
    default_cashback_percentage: Mapped[float] = mapped_column()
    active: Mapped[bool] = mapped_column(server_default=text("true"))


# Optionally add created_at if needed
# created_at = Column(TIMESTAMP(timezone=True), server_default="now()")
