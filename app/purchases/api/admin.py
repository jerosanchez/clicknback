from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.current_user import get_current_admin_user
from app.core.database import get_async_db
from app.core.errors.builders import internal_server_error, unprocessable_entity_error
from app.core.logging import logging
from app.purchases.composition import get_purchase_service
from app.purchases.errors import ErrorCode
from app.purchases.exceptions import InvalidPurchaseStatusException
from app.purchases.schemas import PaginatedPurchaseOut, PurchaseAdminOut
from app.purchases.services import PurchaseService
from app.users.models import User

router = APIRouter(prefix="/purchases", tags=["purchases"])


@router.get(
    "/",
    description="List all purchases across all users. Admin access required.",
)
async def list_all_purchases(
    status: str | None = Query(
        None, description="Filter by status: pending, confirmed, or reversed."
    ),
    user_id: str | None = Query(None, description="Filter by user ID."),
    merchant_id: str | None = Query(None, description="Filter by merchant ID."),
    start_date: date | None = Query(
        None,
        description="Inclusive lower bound on created_at (ISO 8601 date: YYYY-MM-DD).",
    ),
    end_date: date | None = Query(
        None,
        description="Inclusive upper bound on created_at (ISO 8601 date: YYYY-MM-DD).",
    ),
    page: int = Query(1, ge=1, description="Page number (1-based)."),
    page_size: int = Query(
        10, ge=1, le=100, description="Number of results per page (max 100)."
    ),
    service: PurchaseService = Depends(get_purchase_service),
    db: AsyncSession = Depends(get_async_db),
    _: User = Depends(get_current_admin_user),
) -> PaginatedPurchaseOut:
    try:
        items, total = await service.list_purchases(
            db,
            status=status,
            user_id=user_id,
            merchant_id=merchant_id,
            start_date=start_date,
            end_date=end_date,
            page=page,
            page_size=page_size,
        )
    except InvalidPurchaseStatusException as e:
        raise unprocessable_entity_error(ErrorCode.INVALID_PURCHASE_STATUS, str(e))

    except Exception as e:
        logging.error(
            "An unexpected error occurred while listing purchases.",
            extra={"error": str(e)},
        )
        raise internal_server_error()

    return PaginatedPurchaseOut(
        items=[PurchaseAdminOut.model_validate(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
    )
