from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.current_user import get_current_admin_user
from app.core.database import get_async_db
from app.core.errors.builders import internal_server_error, not_found_error
from app.core.logging import logging
from app.core.unit_of_work import SQLAlchemyUnitOfWork, UnitOfWorkABC
from app.offers.composition import get_offer_service
from app.offers.exceptions import OfferNotFoundException
from app.offers.schemas import OfferStatusEnum, OfferStatusOut, OfferStatusUpdate
from app.offers.services import OfferService
from app.users.models import User

router = APIRouter(prefix="/offers", tags=["offers"])


def get_unit_of_work(db: AsyncSession = Depends(get_async_db)) -> UnitOfWorkABC:
    return SQLAlchemyUnitOfWork(db)


@router.patch(
    "/{offer_id}/status",
    status_code=status.HTTP_200_OK,
    description="Activate or deactivate an offer.",
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
            "description": "Admin role required.",
            "content": {
                "application/json": {
                    "example": {
                        "error": {
                            "code": "FORBIDDEN",
                            "message": "Admin access required.",
                            "details": {},
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
async def set_offer_status(
    offer_id: str,
    update_data: OfferStatusUpdate,
    offer_service: OfferService = Depends(get_offer_service),
    uow: UnitOfWorkABC = Depends(get_unit_of_work),
    _current_user: User = Depends(get_current_admin_user),
) -> OfferStatusOut:
    active = update_data.status == "active"
    try:
        updated = await offer_service.set_offer_status(offer_id, active, uow)

    except OfferNotFoundException as exc:
        raise not_found_error(
            message=str(exc),
            details={
                "resource_type": "offer",
                "resource_id": offer_id,
            },
        )

    except Exception as e:
        logging.error(
            "An unexpected error occurred while updating offer status.",
            extra={"error": str(e)},
        )
        raise internal_server_error()

    return OfferStatusOut(
        id=UUID(offer_id),
        status=OfferStatusEnum.active if updated.active else OfferStatusEnum.inactive,
    )
