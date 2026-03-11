from datetime import datetime, timezone
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit.enums import AuditAction, AuditActorType, AuditOutcome
from app.core.audit.models import AuditLog
from app.core.audit.repositories import AuditTrailRepositoryABC
from app.core.logging import logger


class AuditTrail:
    """Thin service that persists an audit row and emits a log line together.

    Inject via __init__() into any service that performs critical operations:

        class PurchaseService:
            def __init__(
                self,
                repository: PurchaseRepositoryABC,
                audit_trail: AuditTrail,
            ): ...

    Call record() *after* the business operation succeeds.  If the operation
    raises before reaching record(), no audit row is written — which correctly
    reflects that the operation did not complete.
    """

    def __init__(self, repository: AuditTrailRepositoryABC) -> None:
        self._repository = repository

    async def record(
        self,
        *,
        db: AsyncSession,
        actor_type: AuditActorType,
        actor_id: str | None,
        action: AuditAction,
        resource_type: str,
        resource_id: str,
        outcome: AuditOutcome,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Write one audit row and emit a corresponding INFO log line.

        All parameters are keyword-only to make call sites self-documenting
        and to prevent accidental positional mismatches.

        Args:
            db:            The current async database session.
            actor_type:    Whether the initiator is system, admin, or user.
            actor_id:      UUID of the acting user/admin; None for system operations.
            action:        The AuditAction enum member describing the operation.
            resource_type: Domain entity type (e.g. "purchase", "payout").
            resource_id:   UUID of the affected record.
            outcome:       AuditOutcome.success or AuditOutcome.failure.
            details:       Optional action-specific JSON payload (amounts, reasons, etc.).
        """
        audit_log = AuditLog(
            # Store as naive UTC datetime to match the DateTime() column definition.
            occurred_at=datetime.now(timezone.utc).replace(tzinfo=None),
            actor_type=actor_type.value,
            actor_id=actor_id,
            action=action.value,
            resource_type=resource_type,
            resource_id=resource_id,
            outcome=outcome.value,
            details=details,
        )

        await self._repository.add(db, audit_log)

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
