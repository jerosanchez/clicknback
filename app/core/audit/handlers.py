"""Audit handlers for domain events.

Each handler subscribes (via the message broker) to a specific domain event
and translates it into a persistent audit record.  The mapping from domain
event fields to audit action / actor / outcome lives entirely here, keeping
audit concerns fully encapsulated within the audit module.

Business modules publish their own domain events and remain completely unaware
of the audit module.  See ADR-023.
"""

from datetime import datetime
from typing import Any, Callable

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit.enums import AuditAction, AuditActorType, AuditOutcome
from app.core.audit.models import AuditLog
from app.core.audit.repositories import AuditTrailRepositoryABC
from app.core.events.purchase_events import (
    PurchaseConfirmed,
    PurchaseRejected,
    PurchaseReversed,
)
from app.core.logging import logger


async def _persist_audit_log(
    db: AsyncSession,
    repository: AuditTrailRepositoryABC,
    datetime_provider: Callable[[], datetime],
    *,
    actor_type: AuditActorType,
    actor_id: str | None,
    action: AuditAction,
    resource_type: str,
    resource_id: str,
    outcome: AuditOutcome,
    details: dict[str, Any] | None = None,
) -> None:
    """Persist one audit record and emit a structured log line."""
    dt = datetime_provider()
    if dt.tzinfo is not None:
        dt = dt.astimezone(__import__("datetime").timezone.utc).replace(tzinfo=None)

    audit_log = AuditLog(
        occurred_at=dt,
        actor_type=actor_type.value,
        actor_id=actor_id if actor_type != AuditActorType.system else None,
        action=action.value,
        resource_type=resource_type,
        resource_id=resource_id,
        outcome=outcome.value,
        details=details,
    )

    await repository.add(db, audit_log)

    logger.info(
        "Audit: %s %s on %s/%s → %s",
        actor_type.value,
        action.value,
        resource_type,
        resource_id,
        outcome.value,
        extra={
            "actor_type": actor_type.value,
            "actor_id": actor_id,
            "action": action.value,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "outcome": outcome.value,
        },
    )


async def _handle_purchase_confirmed(
    db: AsyncSession,
    repository: AuditTrailRepositoryABC,
    datetime_provider: Callable[[], datetime],
    event: PurchaseConfirmed,
) -> None:
    """Translate a PurchaseConfirmed domain event into an audit record."""
    await _persist_audit_log(
        db,
        repository,
        datetime_provider,
        actor_type=AuditActorType.system,
        actor_id=None,
        action=AuditAction.PURCHASE_CONFIRMED,
        resource_type="purchase",
        resource_id=event.purchase_id,
        outcome=AuditOutcome.success,
        details={
            "merchant_id": event.merchant_id,
            "amount": str(event.amount),
            "currency": event.currency,
            "cashback_amount": str(event.cashback_amount),
        },
    )


async def _handle_purchase_rejected(
    db: AsyncSession,
    repository: AuditTrailRepositoryABC,
    datetime_provider: Callable[[], datetime],
    event: PurchaseRejected,
) -> None:
    """Translate a PurchaseRejected domain event into an audit record."""
    await _persist_audit_log(
        db,
        repository,
        datetime_provider,
        actor_type=AuditActorType.system,
        actor_id=None,
        action=AuditAction.PURCHASE_REJECTED,
        resource_type="purchase",
        resource_id=event.purchase_id,
        outcome=AuditOutcome.success,
        details={
            "merchant_id": event.merchant_id,
            "amount": str(event.amount),
            "currency": event.currency,
            "reason": event.reason,
        },
    )


async def _handle_purchase_reversed(
    db: AsyncSession,
    repository: AuditTrailRepositoryABC,
    datetime_provider: Callable[[], datetime],
    event: PurchaseReversed,
) -> None:
    """Translate a PurchaseReversed domain event into an audit record."""
    await _persist_audit_log(
        db,
        repository,
        datetime_provider,
        actor_type=AuditActorType.admin,
        actor_id=event.admin_id,
        action=AuditAction.PURCHASE_REVERSED,
        resource_type="purchase",
        resource_id=event.purchase_id,
        outcome=AuditOutcome.success,
        details={"prior_status": event.prior_status},
    )
