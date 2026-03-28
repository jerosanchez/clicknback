from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.current_user import get_current_admin_user
from app.core.database import get_async_db
from app.core.errors.builders import internal_server_error, unprocessable_entity_error
from app.core.logging import logging
from app.core.unit_of_work import SQLAlchemyUnitOfWork, UnitOfWorkABC
from app.feature_flags.composition import get_feature_flag_service
from app.feature_flags.errors import ErrorCode
from app.feature_flags.exceptions import FeatureFlagScopeIdRequiredException
from app.feature_flags.schemas import (
    FeatureFlagKeyValidator,
    FeatureFlagOut,
    FeatureFlagSet,
)
from app.feature_flags.services import FeatureFlagService
from app.users.models import User

router = APIRouter(prefix="/feature-flags", tags=["feature-flags"])


def get_unit_of_work(db: AsyncSession = Depends(get_async_db)) -> UnitOfWorkABC:
    return SQLAlchemyUnitOfWork(db)


@router.put(
    "/{key}",
    status_code=status.HTTP_200_OK,
    description="Create or update a feature flag (upsert by key + scope).",
)
async def set_feature_flag(
    key: str,
    body: FeatureFlagSet,
    feature_flag_service: FeatureFlagService = Depends(get_feature_flag_service),
    uow: UnitOfWorkABC = Depends(get_unit_of_work),
    _current_user: User = Depends(get_current_admin_user),
) -> FeatureFlagOut:
    # Validate key format via FeatureFlagKeyValidator
    try:
        FeatureFlagKeyValidator(key=key)
    except Exception:
        raise unprocessable_entity_error(
            code="VALIDATION_ERROR",
            message="Invalid feature flag key.",
            details={"key": key},
        )

    try:
        flag = await feature_flag_service.set_flag(key, body, uow)

    except FeatureFlagScopeIdRequiredException as exc:
        raise unprocessable_entity_error(
            code=ErrorCode.FEATURE_FLAG_SCOPE_ID_REQUIRED,
            message=str(exc),
            details={"scope_type": exc.scope_type},
        )

    except Exception as exc:
        logging.error(
            "Unexpected error while setting feature flag.",
            extra={"error": str(exc)},
        )
        raise internal_server_error()

    return FeatureFlagOut.model_validate(flag)
