from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.current_user import get_current_user
from app.core.database import get_async_db
from app.core.errors.builders import internal_server_error
from app.core.logging import logging
from app.core.schemas import PaginationOut
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
    responses={
        401: {
            "description": "Missing or invalid authentication token.",
            "content": {
                "application/json": {
                    "example": {
                        "error": {
                            "code": "INVALID_TOKEN",
                            "message": (
                                "Invalid token, or user does not have"
                                " permissions to perform this action."
                            ),
                            "details": {},
                        }
                    }
                }
            },
        },
        422: {
            "description": "Request parameter type validation failed (e.g. non-integer offset).",
            "content": {
                "application/json": {
                    "example": {
                        "error": {
                            "code": "VALIDATION_ERROR",
                            "message": "Request validation failed.",
                            "details": {
                                "violations": [
                                    {
                                        "field": "offset",
                                        "reason": (
                                            "Input should be greater than or equal to 0"
                                        ),
                                    }
                                ]
                            },
                        }
                    }
                }
            },
        },
        500: {
            "description": "Unexpected server error.",
            "content": {
                "application/json": {
                    "example": {
                        "error": {
                            "code": "INTERNAL_SERVER_ERROR",
                            "message": (
                                "An unexpected error occurred."
                                " Our team has been notified. Please retry later."
                            ),
                            "details": {
                                "request_id": "not available",
                                "timestamp": "2026-04-21T10:00:00.000000",
                            },
                        }
                    }
                }
            },
        },
    },
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
