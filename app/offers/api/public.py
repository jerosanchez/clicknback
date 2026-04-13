from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.current_user import get_current_user
from app.core.database import get_async_db
from app.core.errors.builders import (
    forbidden_error,
    internal_server_error,
    not_found_error,
)
from app.core.logging import logging
from app.core.schemas import PaginationOut
from app.offers.composition import get_offer_service
from app.offers.exceptions import (
    InactiveMerchantForOfferException,
    InactiveOfferException,
    OfferNotFoundException,
)
from app.offers.models import Offer
from app.offers.schemas import (
    ActiveOfferOut,
    CashbackTypeEnum,
    OfferDetailsOut,
    OfferStatusEnum,
    PaginatedActiveOffersOut,
)
from app.offers.services import OfferService
from app.users.models import User, UserRoleEnum

router = APIRouter(prefix="/offers", tags=["offers"])


@router.get(
    "/active",
    status_code=status.HTTP_200_OK,
    description=(
        "List all currently active offers visible to end-users."
        " Filters: offer active, merchant active, and today within [start_date, end_date]."
    ),
)
async def list_active_offers(
    offset: int = Query(default=0, ge=0, description="Number of results to skip."),
    limit: int = Query(
        default=settings.default_page_size,
        ge=1,
        le=settings.max_page_size,
        description=f"Number of results to return (max {settings.max_page_size}).",
    ),
    offer_service: OfferService = Depends(get_offer_service),
    db: AsyncSession = Depends(get_async_db),
    _current_user: User = Depends(get_current_user),
) -> PaginatedActiveOffersOut:
    try:
        items, total = await offer_service.list_active_offers(
            offset,
            limit,
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
        data=[
            _map_to_active_offer_out(offer, merchant_name)
            for offer, merchant_name in items
        ],
        pagination=PaginationOut(offset=offset, limit=limit, total=total),
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


@router.get(
    "/{offer_id}",
    status_code=status.HTTP_200_OK,
    description=(
        "Get detailed information about a specific offer."
        " Active offers are visible to all authenticated users."
        " Admin users can also view inactive offers."
    ),
)
async def get_offer_details(
    offer_id: str,
    offer_service: OfferService = Depends(get_offer_service),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
) -> OfferDetailsOut:
    is_admin = current_user.role == UserRoleEnum.admin
    try:
        offer, merchant_name = await offer_service.get_offer_details(
            offer_id, is_admin, db
        )

    except OfferNotFoundException as exc:
        raise not_found_error(
            message=str(exc),
            details={
                "resource_type": "offer",
                "resource_id": offer_id,
            },
        )

    except InactiveOfferException:
        raise forbidden_error(
            message="You do not have permission to view this offer.",
            details={
                "resource_type": "offer",
                "resource_id": offer_id,
                "reason": "This offer is inactive. Only admin users can view inactive offers.",
            },
        )
    except InactiveMerchantForOfferException:
        raise forbidden_error(
            message="You do not have permission to view this offer.",
            details={
                "resource_type": "offer",
                "resource_id": offer_id,
                "reason": "The merchant for this offer is inactive. Only admin users can view offers from inactive merchants.",
            },
        )

    except Exception as e:
        logging.error(
            "An unexpected error occurred while retrieving offer details.",
            extra={"error": str(e)},
        )
        raise internal_server_error()

    return _map_to_offer_details_out(offer, merchant_name)


def _map_to_offer_details_out(offer: Offer, merchant_name: str) -> OfferDetailsOut:
    return OfferDetailsOut(
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
        status=OfferStatusEnum.active if offer.active else OfferStatusEnum.inactive,
    )
