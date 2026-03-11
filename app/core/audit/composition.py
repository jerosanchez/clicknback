from app.core.audit.repositories import AuditTrailRepository
from app.core.audit.services import AuditTrail


def get_audit_trail() -> AuditTrail:
    """FastAPI Depends factory for AuditTrail.

    Example usage in composition.py:

        def get_purchase_service(
            audit_trail: AuditTrail = Depends(get_audit_trail),
        ) -> PurchaseService:
            return PurchaseService(
                repository=PurchaseRepository(),
                audit_trail=audit_trail,
            )
    """
    return AuditTrail(repository=AuditTrailRepository())
