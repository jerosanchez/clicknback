from abc import ABC, abstractmethod

from sqlalchemy import ColumnElement, select
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
    ) -> tuple[list[FeatureFlag], int]:
        """List feature flags with optional filters.

        Returns: (flags, total_count)
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
        select_stmt = select_stmt.order_by(FeatureFlag.created_at.desc())

        result = await db.execute(select_stmt)
        flags = list(result.scalars().all())

        return flags, total
