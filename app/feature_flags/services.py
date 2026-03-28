from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import logger
from app.core.unit_of_work import UnitOfWorkABC
from app.feature_flags.models import FeatureFlag
from app.feature_flags.policies import validate_scope_id_required
from app.feature_flags.repositories import FeatureFlagRepositoryABC
from app.feature_flags.schemas import FeatureFlagSet


class FeatureFlagService:
    def __init__(self, repository: FeatureFlagRepositoryABC) -> None:
        self._repository = repository

    async def set_flag(
        self,
        key: str,
        data: FeatureFlagSet,
        uow: UnitOfWorkABC,
    ) -> FeatureFlag:
        scope_type = data.scope_type
        scope_id = str(data.scope_id) if data.scope_id is not None else None

        validate_scope_id_required(scope_type, scope_id)

        existing = await self._repository.get_by_key_and_scope(
            uow.session, key, scope_type, scope_id
        )

        if existing is not None:
            existing.enabled = data.enabled
            if data.description is not None:
                existing.description = data.description
            flag = await self._repository.upsert(uow.session, existing)
        else:
            flag = FeatureFlag(
                key=key,
                enabled=data.enabled,
                scope_type=scope_type,
                scope_id=scope_id,
                description=data.description,
            )
            flag = await self._repository.upsert(uow.session, flag)

        await uow.commit()
        logger.info(
            "Feature flag set.",
            extra={"key": key, "scope_type": scope_type, "scope_id": scope_id},
        )
        return flag

    async def is_enabled(
        self,
        key: str,
        db: AsyncSession,
        scope_type: str = "global",
        scope_id: str | None = None,
    ) -> bool:
        """Resolve flag with fail-open semantics.

        Resolution order:
        1. Scoped flag (matching key + scope_type + scope_id)
        2. Global flag (matching key, scope_type='global')
        3. Default: True (fail-open)
        """
        if scope_type != "global" and scope_id is not None:
            scoped = await self._repository.get_by_key_and_scope(
                db, key, scope_type, scope_id
            )
            if scoped is not None:
                return scoped.enabled

        global_flag = await self._repository.get_by_key_and_scope(
            db, key, "global", None
        )
        if global_flag is not None:
            return global_flag.enabled

        return True
