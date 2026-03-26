from datetime import datetime, timezone

from app.core.audit.handlers import (
    _handle_purchase_confirmed,
    _handle_purchase_rejected,
    _handle_purchase_reversed,
)
from app.core.audit.repositories import AuditTrailRepository
from app.core.broker import MessageBrokerABC
from app.core.database import AsyncSessionLocal
from app.core.events.purchase_events import (
    PurchaseConfirmed,
    PurchaseRejected,
    PurchaseReversed,
)


def subscribe_audit_handlers(broker: MessageBrokerABC) -> None:
    """Subscribe audit handlers to all auditable domain events.

    Call this during application startup (in app/main.py lifespan) to wire
    the audit module to the message broker.  Each handler translates one
    domain event type into a persistent audit log record.

    Business modules remain completely unaware of the audit module — they
    publish their own domain events, and the audit module subscribes here.

    Args:
        broker: The message broker instance to register handlers with.
    """
    repository = AuditTrailRepository()

    def datetime_provider() -> datetime:
        """Provide current UTC datetime."""
        return datetime.now(timezone.utc)

    async def on_purchase_confirmed(event: PurchaseConfirmed) -> None:
        async with AsyncSessionLocal() as db:
            await _handle_purchase_confirmed(
                db=db,
                repository=repository,
                datetime_provider=datetime_provider,
                event=event,
            )

    async def on_purchase_rejected(event: PurchaseRejected) -> None:
        async with AsyncSessionLocal() as db:
            await _handle_purchase_rejected(
                db=db,
                repository=repository,
                datetime_provider=datetime_provider,
                event=event,
            )

    async def on_purchase_reversed(event: PurchaseReversed) -> None:
        async with AsyncSessionLocal() as db:
            await _handle_purchase_reversed(
                db=db,
                repository=repository,
                datetime_provider=datetime_provider,
                event=event,
            )

    broker.subscribe(PurchaseConfirmed, on_purchase_confirmed)
    broker.subscribe(PurchaseRejected, on_purchase_rejected)
    broker.subscribe(PurchaseReversed, on_purchase_reversed)
