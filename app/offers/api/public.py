from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.current_user import get_current_user
from app.core.database import get_db
from app.core.errors.builders import internal_server_error
from app.core.logging import logging
from app.offers.composition import get_offer_service
from app.offers.models import Offer
from app.offers.schemas import (
    ActiveOfferOut,
    CashbackTypeEnum,
    PaginatedActiveOffersOut,
)
from app.offers.services import OfferService
from app.users.models import User

router = APIRouter(prefix="/offers", tags=["offers"])


@router.get(
    "/active",
    status_code=status.HTTP_200_OK,
    description=(
        "List all currently active offers visible to end-users."
        " Filters: offer active, merchant active, and today within [start_date, end_date]."
    ),
)
def list_active_offers(
    page: int = Query(default=1, ge=1, description="Page number (1-indexed)."),
    page_size: int = Query(
        default=settings.default_page_size,
        ge=1,
        le=settings.max_page_size,
        description=f"Number of results per page (max {settings.max_page_size}).",
    ),
    offer_service: OfferService = Depends(get_offer_service),
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> PaginatedActiveOffersOut:
    try:
        items, total = offer_service.list_active_offers(
            page,
            page_size,
            date.today(),
            db,
        )
    except Exception as e:
        logging.error(
            "An unexpected error occurred while listing active offers.",
            extra={"error": str(e)},
        )
        raise internal_server_error()

    return PaginatedActiveOffersOut(
        offers=[
            _map_to_active_offer_out(offer, merchant_name)
            for offer, merchant_name in items
        ],
        total=total,
        page=page,
        page_size=page_size,
    )


def _map_to_active_offer_out(offer: Offer, merchant_name: str) -> ActiveOfferOut:
    return ActiveOfferOut(
        id=UUID(offer.id),
        merchant_name=merchant_name,
        cashback_type=(
            CashbackTypeEnum.fixed
            if offer.fixed_amount is not None
            else CashbackTypeEnum.percent
        ),
        cashback_value=(
            offer.fixed_amount if offer.fixed_amount is not None else offer.percentage
        ),
        monthly_cap=offer.monthly_cap_per_user,
        start_date=offer.start_date,
        end_date=offer.end_date,
    )
