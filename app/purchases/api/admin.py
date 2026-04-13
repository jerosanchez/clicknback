from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.current_user import get_current_admin_user
from app.core.database import get_async_db
from app.core.errors.builders import (
    internal_server_error,
    not_found_error,
    unprocessable_entity_error,
    validation_error,
)
from app.core.logging import logging
from app.core.schemas import PaginationOut
from app.core.unit_of_work import UnitOfWorkABC
from app.purchases.composition import get_purchase_service, get_unit_of_work
from app.purchases.errors import ErrorCode
from app.purchases.exceptions import (
    InvalidPurchaseStatusException,
    PurchaseAlreadyReversedException,
    PurchaseNotFoundException,
    PurchaseNotPendingException,
)
from app.purchases.schemas import PaginatedPurchaseOut, PurchaseAdminOut, PurchaseOut
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
    offset: int = Query(0, ge=0, description="Number of results to skip."),
    limit: int = Query(
        10, ge=1, le=100, description="Number of results to return (max 100)."
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
            offset=offset,
            limit=limit,
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
        data=[PurchaseAdminOut.model_validate(item) for item in items],
        pagination=PaginationOut(offset=offset, limit=limit, total=total),
    )


@router.patch(
    "/{purchase_id}/reverse",
    description="Reverse a purchase and its associated cashback. Admin access required.",
)
async def reverse_purchase(
    purchase_id: str,
    service: PurchaseService = Depends(get_purchase_service),
    uow: UnitOfWorkABC = Depends(get_unit_of_work),
    current_admin: User = Depends(get_current_admin_user),
) -> PurchaseOut:
    try:
        purchase = await service.reverse_purchase(
            purchase_id, str(current_admin.id), uow
        )
    except PurchaseNotFoundException as exc:
        raise not_found_error(
            message=f"Purchase with ID '{exc.purchase_id}' does not exist.",
            details={"resource_type": "purchase", "resource_id": exc.purchase_id},
        ) from None
    except PurchaseAlreadyReversedException as exc:
        raise validation_error(
            code=ErrorCode.PURCHASE_ALREADY_REVERSED,
            message=str(exc),
            details=[
                {
                    "purchase_id": exc.purchase_id,
                    "current_status": exc.current_status,
                    "reversible_from_statuses": exc.reversible_from_statuses,
                }
            ],
        ) from None
    except Exception as e:
        logging.error(
            "An unexpected error occurred while reversing purchase.",
            extra={"error": str(e), "purchase_id": purchase_id},
        )
        raise internal_server_error()

    return PurchaseOut(
        id=purchase.id,
        status=purchase.status,
        cashback_amount=purchase.cashback_amount,
    )


@router.post(
    "/{purchase_id}/confirmation",
    description="Manually confirm a pending purchase and credit cashback. Admin access required.",
)
async def admin_confirm_purchase(
    purchase_id: str,
    service: PurchaseService = Depends(get_purchase_service),
    uow: UnitOfWorkABC = Depends(get_unit_of_work),
    current_admin: User = Depends(get_current_admin_user),
) -> PurchaseOut:
    try:
        purchase = await service.confirm_purchase_manually(
            purchase_id, str(current_admin.id), uow
        )
    except PurchaseNotFoundException as exc:
        raise not_found_error(
            message=f"Purchase with ID '{exc.purchase_id}' does not exist.",
            details={"resource_type": "purchase", "resource_id": exc.purchase_id},
        ) from None
    except PurchaseNotPendingException as exc:
        raise validation_error(
            code=ErrorCode.PURCHASE_NOT_PENDING,
            message=str(exc),
            details=[
                {
                    "purchase_id": exc.purchase_id,
                    "current_status": exc.current_status,
                    "required_status": exc.required_status,
                }
            ],
        ) from None
    except Exception as e:
        logging.error(
            "An unexpected error occurred while confirming purchase.",
            extra={"error": str(e), "purchase_id": purchase_id},
        )
        raise internal_server_error()

    return PurchaseOut(
        id=purchase.id,
        status=purchase.status,
        cashback_amount=purchase.cashback_amount,
    )
