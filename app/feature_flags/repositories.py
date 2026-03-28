from abc import ABC, abstractmethod

from sqlalchemy import select
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
