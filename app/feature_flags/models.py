import uuid
from datetime import datetime

from sqlalchemy import Column, Index, String, func, text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql.sqltypes import TIMESTAMP

from app.core.database import Base


class FeatureFlag(Base):
    __tablename__ = "feature_flags"

    id: Mapped[str] = mapped_column(
        primary_key=True, index=True, default=lambda: str(uuid.uuid4())
    )
    key: Mapped[str] = mapped_column(nullable=False)
    enabled: Mapped[bool] = mapped_column(server_default=text("true"))
    scope_type: Mapped[str] = mapped_column(server_default=text("'global'"))
    scope_id: Mapped[str | None] = mapped_column(nullable=True)
    description: Mapped[str | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True), server_default=text("now()")
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True),
        server_default=text("now()"),
        onupdate=func.now(),
    )

    __table_args__ = (
        # Functional unique index using COALESCE so that two global flags (both
        # with scope_id=NULL) are treated as duplicates. A plain UNIQUE constraint
        # would allow multiple NULLs because NULL ≠ NULL in SQL.
        Index(
            "uq_feature_flags_key_scope",
            "key",
            "scope_type",
            func.coalesce(Column("scope_id", String), ""),
            unique=True,
        ),
        Index("ix_feature_flags_key_scope_lookup", "key", "scope_type", "scope_id"),
    )
