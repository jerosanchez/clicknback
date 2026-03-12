"""Purchase outcome processor.

Applies a resolved verification outcome: updates the purchase status in the
DB, publishes the domain event, and writes the audit trail row.  No retry
awareness — both functions receive a final decision and act on it.
"""

from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit.enums import AuditAction, AuditActorType, AuditOutcome
from app.core.audit.services import AuditTrailABC
from app.core.broker import MessageBrokerABC
from app.core.events.purchase_events import PurchaseConfirmed, PurchaseRejected
from app.core.logging import logger
from app.purchases.models import Purchase
from app.purchases.repositories import PurchaseRepositoryABC
from app.purchases.schemas import PurchaseStatus


async def _confirm_purchase(
    *,
    purchase: Purchase,
    verified_at: datetime,
    db: AsyncSession,
    repository: PurchaseRepositoryABC,
    audit_trail: AuditTrailABC,
    broker: MessageBrokerABC,
) -> None:
    """Update status to confirmed, publish the domain event, and record the audit row."""
    await repository.update_status(db, purchase.id, PurchaseStatus.CONFIRMED.value)

    await broker.publish(
        PurchaseConfirmed(
            purchase_id=purchase.id,
            user_id=purchase.user_id,
            merchant_id=purchase.merchant_id,
            amount=purchase.amount,
            verified_at=verified_at,
        )
    )

    await audit_trail.record(
        db=db,
        actor_type=AuditActorType.system,
        actor_id=None,
        action=AuditAction.PURCHASE_CONFIRMED,
        resource_type="purchase",
        resource_id=purchase.id,
        outcome=AuditOutcome.success,
        details={
            "merchant_id": purchase.merchant_id,
            "amount": str(purchase.amount),
            "currency": purchase.currency,
        },
    )

    logger.info(
        "verify_purchases: purchase confirmed.",
        extra={"purchase_id": purchase.id, "merchant_id": purchase.merchant_id},
    )


async def _reject_purchase(
    *,
    purchase: Purchase,
    reason: str,
    attempt: int,
    failed_at: datetime,
    db: AsyncSession,
    repository: PurchaseRepositoryABC,
    audit_trail: AuditTrailABC,
    broker: MessageBrokerABC,
) -> None:
    """Update status to rejected, publish the domain event, and record the audit row."""
    await repository.update_status(db, purchase.id, PurchaseStatus.REJECTED.value)

    await broker.publish(
        PurchaseRejected(
            purchase_id=purchase.id,
            user_id=purchase.user_id,
            merchant_id=purchase.merchant_id,
            amount=purchase.amount,
            failed_at=failed_at,
            reason=reason,
        )
    )

    await audit_trail.record(
        db=db,
        actor_type=AuditActorType.system,
        actor_id=None,
        action=AuditAction.PURCHASE_REJECTED,
        resource_type="purchase",
        resource_id=purchase.id,
        outcome=AuditOutcome.success,
        details={
            "merchant_id": purchase.merchant_id,
            "amount": str(purchase.amount),
            "currency": purchase.currency,
            "reason": reason,
            "attempt": attempt,
        },
    )

    logger.info(
        "verify_purchases: purchase rejected.",
        extra={"purchase_id": purchase.id, "merchant_id": purchase.merchant_id},
    )
