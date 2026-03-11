"""SQLAlchemy ORM model for the append-only audit_logs table."""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import Index, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class AuditLog(Base):
    """Append-only audit record. Never updated or deleted after creation."""

    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(primary_key=True, default=lambda: str(uuid.uuid4()))
    occurred_at: Mapped[datetime] = mapped_column()
    actor_type: Mapped[str] = mapped_column(String(16))
    # Null when actor_type == AuditActorType.system (no human actor)
    actor_id: Mapped[str | None] = mapped_column(String, nullable=True)
    action: Mapped[str] = mapped_column(String(64))
    resource_type: Mapped[str] = mapped_column(String(64))
    resource_id: Mapped[str] = mapped_column(String)
    outcome: Mapped[str] = mapped_column(String(16))
    # Action-specific payload: amounts, status changes, rejection reasons, etc.
    details: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)

    __table_args__ = (
        Index("ix_audit_logs_action", "action"),
        Index("ix_audit_logs_actor_id", "actor_id"),
        Index("ix_audit_logs_occurred_at", "occurred_at"),
        Index("ix_audit_logs_resource", "resource_type", "resource_id"),
    )
