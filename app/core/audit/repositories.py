from abc import ABC, abstractmethod

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit.models import AuditLog


class AuditTrailRepositoryABC(ABC):
    @abstractmethod
    async def add(self, db: AsyncSession, audit_log: AuditLog) -> None:
        """Persist an audit log entry."""


class AuditTrailRepository(AuditTrailRepositoryABC):
    async def add(self, db: AsyncSession, audit_log: AuditLog) -> None:
        db.add(audit_log)
        await db.commit()
