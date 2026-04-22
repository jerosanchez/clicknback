from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.current_user import get_current_user
from app.core.database import get_async_db
from app.core.errors.builders import (
    forbidden_error,
    internal_server_error,
    not_found_error,
)
from app.core.logging import logging
from app.offers.composition import get_offer_service
from app.offers.exceptions import (
    InactiveMerchantForOfferException,
    InactiveOfferException,
    OfferNotFoundException,
)
from app.offers.models import Offer
from app.offers.schemas import CashbackTypeEnum, OfferDetailsOut, OfferStatusEnum
from app.offers.services import OfferService
from app.users.models import User, UserRoleEnum

router = APIRouter(prefix="/offers", tags=["offers"])


@router.get(
    "/{offer_id}",
    status_code=status.HTTP_200_OK,
    description=(
        "Get detailed information about a specific offer."
        " Active offers are visible to all authenticated users."
        " Admin users can also view inactive offers."
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
        403: {
            "description": (
                "Offer is inactive or merchant is inactive;"
                " only admin users can view such offers."
            ),
            "content": {
                "application/json": {
                    "example": {
                        "error": {
                            "code": "FORBIDDEN",
                            "message": "You do not have permission to view this offer.",
                            "details": {
                                "resource_type": "offer",
                                "resource_id": "00000000-0000-0000-0000-000000000000",
                                "reason": (
                                    "This offer is inactive."
                                    " Only admin users can view inactive offers."
                                ),
                            },
                        }
                    }
                }
            },
        },
        404: {
            "description": "Offer not found.",
            "content": {
                "application/json": {
                    "example": {
                        "error": {
                            "code": "NOT_FOUND",
                            "message": "Offer not found.",
                            "details": {
                                "resource_type": "offer",
                                "resource_id": "00000000-0000-0000-0000-000000000000",
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
                "reason": (
                    "The merchant for this offer is inactive."
                    " Only admin users can view offers from inactive merchants."
                ),
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
