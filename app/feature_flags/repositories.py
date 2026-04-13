from abc import ABC, abstractmethod
from typing import List

from sqlalchemy import ColumnElement, and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.feature_flags.models import FeatureFlag


class FeatureFlagRepositoryABC(ABC):
    @abstractmethod
    async def get_by_key_and_scope(
        self,
        db: AsyncSession,
        key: str,
        scope_type: str,
        scope_id: str | None,
    ) -> FeatureFlag | None:
        pass

    @abstractmethod
    async def upsert(
        self,
        db: AsyncSession,
        flag: FeatureFlag,
    ) -> FeatureFlag:
        pass

    @abstractmethod
    async def list(
        self,
        db: AsyncSession,
        key: str | None = None,
        scope_type: str | None = None,
        scope_id: str | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> tuple[list[FeatureFlag], int]:
        """List feature flags with optional filters.

        Returns: (flags, total_count)
        """
        pass

    @abstractmethod
    async def get_multiple_by_key_and_scopes(
        self,
        db: AsyncSession,
        key: str,
        scope_specs: List[tuple[str, str | None]],
    ) -> List[FeatureFlag]:
        """Fetch flags for multiple scopes in a single optimized query.

        Fetches all flags matching the key and any of the given scope_specs,
        plus the global flag as fallback. Used for batch evaluation.

        Args:
            db: AsyncSession for database queries
            key: Feature flag key (e.g., "purchase_auto_confirm")
            scope_specs: List of (scope_type, scope_id) tuples to check

        Returns:
            List of matching FeatureFlag objects (may include the global flag)
        """
        pass


class FeatureFlagRepository(FeatureFlagRepositoryABC):
    async def get_by_key_and_scope(
        self,
        db: AsyncSession,
        key: str,
        scope_type: str,
        scope_id: str | None,
    ) -> FeatureFlag | None:
        stmt = select(FeatureFlag).where(
            FeatureFlag.key == key,
            FeatureFlag.scope_type == scope_type,
            FeatureFlag.scope_id == scope_id,
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def upsert(
        self,
        db: AsyncSession,
        flag: FeatureFlag,
    ) -> FeatureFlag:
        db.add(flag)
        await db.flush()
        await db.refresh(flag)
        return flag

    async def list(
        self,
        db: AsyncSession,
        key: str | None = None,
        scope_type: str | None = None,
        scope_id: str | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> tuple[list[FeatureFlag], int]:
        """List feature flags with optional filters.

        All filters are combined with AND semantics.
        """
        filters: list[ColumnElement[bool]] = []

        if key is not None:
            filters.append(FeatureFlag.key == key)

        if scope_type is not None:
            filters.append(FeatureFlag.scope_type == scope_type)

        if scope_id is not None:
            filters.append(FeatureFlag.scope_id == scope_id)

        # Count query
        count_stmt = select(FeatureFlag)
        if filters:
            count_stmt = count_stmt.where(*filters)
        count_result = await db.execute(count_stmt)
        total = len(count_result.scalars().all())

        # Fetch query
        select_stmt = select(FeatureFlag)
        if filters:
            select_stmt = select_stmt.where(*filters)
        select_stmt = (
            select_stmt.order_by(FeatureFlag.created_at.desc())
            .offset(offset)
            .limit(limit)
        )

        result = await db.execute(select_stmt)
        flags = list(result.scalars().all())

        return flags, total

    async def get_multiple_by_key_and_scopes(
        self,
        db: AsyncSession,
        key: str,
        scope_specs: List[tuple[str, str | None]],
    ) -> List[FeatureFlag]:
        """Fetch flags for multiple scopes in a single optimized query.

        Returns all flags matching the key and any of the scope_specs,
        plus the global flag as fallback. Optimized to use a single query
        with OR conditions instead of N+1 queries.
        """
        if not scope_specs:
            return []

        # Build conditions for each (scope_type, scope_id) pair
        scope_conditions = [
            and_(
                FeatureFlag.scope_type == scope_type,
                FeatureFlag.scope_id == scope_id,
            )
            for scope_type, scope_id in scope_specs
        ]

        # Always include the global flag as fallback
        scope_conditions.append(
            and_(
                FeatureFlag.scope_type == "global",
                FeatureFlag.scope_id is None,
            )
        )

        # Fetch all matching flags in one query
        stmt = select(FeatureFlag).where(
            FeatureFlag.key == key,
            or_(*scope_conditions),
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())
