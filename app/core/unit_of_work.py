from abc import ABC, abstractmethod

from sqlalchemy.ext.asyncio import AsyncSession


class UnitOfWorkABC(ABC):
    """Manages a single database transaction boundary.

    Repositories and clients flush SQL changes to ``session`` but never commit.
    Services do not call ``commit()`` or ``rollback()`` directly; instead, they
    rely on a Unit of Work (UoW) collaborator to manage transaction boundaries.
    The UoW is responsible for committing once all participating writes are complete,
    or rolling back on failure.

    This keeps SQLAlchemy session details—and the decision of *when* to commit—
    out of both services and repositories, preventing DB implementation details
    from leaking into business-logic layers (see ADR-021).
    """

    @property
    @abstractmethod
    def session(self) -> AsyncSession:
        """The active SQLAlchemy async session for this unit of work."""

    @abstractmethod
    async def commit(self) -> None:
        """Commit the current transaction, persisting all changes."""

    @abstractmethod
    async def rollback(self) -> None:
        """Rollback the current transaction, discarding all changes."""


class SQLAlchemyUnitOfWork(UnitOfWorkABC):
    """SQLAlchemy implementation — wraps an existing ``AsyncSession``."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    @property
    def session(self) -> AsyncSession:
        """The active SQLAlchemy async session for this unit of work."""
        return self._session

    async def commit(self) -> None:
        """Commit the current transaction, persisting all changes."""
        await self._session.commit()

    async def rollback(self) -> None:
        """Rollback the current transaction, discarding all changes."""
        await self._session.rollback()
