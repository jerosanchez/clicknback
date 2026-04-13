from typing import List

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

    async def list_flags(
        self,
        db: AsyncSession,
        key: str | None = None,
        scope_type: str | None = None,
        scope_id: str | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> tuple[list[FeatureFlag], int]:
        """List feature flags with optional filters."""
        return await self._repository.list(db, key, scope_type, scope_id, offset, limit)

    async def evaluate_scopes(
        self,
        key: str,
        db: AsyncSession,
        scopes: List[tuple[str, str | None]],
    ) -> dict[tuple[str, str | None], bool]:
        """Evaluate feature flag for multiple scopes in a single batch query.

        Returns a dict mapping each (scope_type, scope_id) → enabled state.
        Resolution order for each scope: scoped flag > global flag > fail-open True.

        Args:
            key: Feature flag key
            db: AsyncSession for database queries
            scopes: List of (scope_type, scope_id) tuples to evaluate

        Returns:
            Dict mapping each scope to its resolved enabled state (True if enabled
            or absent, False if explicitly disabled).
        """
        if not scopes:
            return {}

        # Fetch all relevant flags in one optimized query
        flags = await self._repository.get_multiple_by_key_and_scopes(db, key, scopes)

        # Separate scoped and global flags
        global_flag = None
        scoped_flags = {}
        for flag in flags:
            if flag.scope_type == "global":
                global_flag = flag
            else:
                scoped_flags[(flag.scope_type, flag.scope_id)] = flag

        # Resolve each scope: scoped flag > global flag > fail-open True
        results = {}
        for scope_type, scope_id in scopes:
            # Check scoped flag first
            if (scope_type, scope_id) in scoped_flags:
                results[(scope_type, scope_id)] = scoped_flags[
                    (scope_type, scope_id)
                ].enabled
                continue

            # Fall back to global flag
            if global_flag is not None:
                results[(scope_type, scope_id)] = global_flag.enabled
                continue

            # No flag found - fail-open (default to True)
            results[(scope_type, scope_id)] = True

        return results
