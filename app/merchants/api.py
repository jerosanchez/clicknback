from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.current_user import get_current_admin_user
from app.core.database import get_db
from app.core.errors.builders import (
    business_rule_violation_error,
    internal_server_error,
)
from app.core.errors.codes import ErrorCode
from app.core.logging import logging
from app.merchants.composition import get_merchant_service
from app.merchants.exceptions import CashbackPercentageNotValidException
from app.merchants.schemas import MerchantCreate, MerchantOut, PaginatedMerchantsOut
from app.merchants.services import MerchantService
from app.users.models import User

router = APIRouter(prefix="/api/v1")


@router.post("/merchants", status_code=status.HTTP_201_CREATED)
def create_merchant(
    create_data: MerchantCreate,
    merchant_service: MerchantService = Depends(get_merchant_service),
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_admin_user),
) -> MerchantOut:
    try:
        new_merchant = merchant_service.create_merchant(create_data.model_dump(), db)

    except CashbackPercentageNotValidException as exc:
        logging.debug(
            "Failed to create merchant due to invalid cashback percentage.",
            extra={"error": str(exc)},
        )
        raise business_rule_violation_error(
            code=ErrorCode.VALIDATION_ERROR,
            message="Cashback percentage not valid.",
            details={
                "field": "default_cashback_percentage",
                "reason": str(exc),
            },
        )

    except Exception as e:
        logging.error(
            "An unexpected error occurred while creating a merchant.",
            extra={"error": str(e)},
        )
        raise internal_server_error()

    return new_merchant


@router.get("/merchants", status_code=status.HTTP_200_OK)
def list_merchants(
    page: int = Query(default=1, ge=1, description="Page number (1-indexed)."),
    page_size: int = Query(
        default=settings.default_page_size,
        ge=1,
        le=settings.max_page_size,
        description=f"Number of results per page (max {settings.max_page_size}).",
    ),
    active: bool | None = Query(default=None, description="Filter by active status."),
    merchant_service: MerchantService = Depends(get_merchant_service),
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_admin_user),
) -> PaginatedMerchantsOut:
    try:
        items, total = merchant_service.list_merchants(page, page_size, active, db)

    except Exception as e:
        logging.error(
            "An unexpected error occurred while listing merchants.",
            extra={"error": str(e)},
        )
        raise internal_server_error()

    return PaginatedMerchantsOut(
        items=[MerchantOut.model_validate(m) for m in items],
        total=total,
        page=page,
        page_size=page_size,
    )
