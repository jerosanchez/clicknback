from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.current_user import get_current_user
from app.core.database import get_async_db
from app.core.errors.builders import internal_server_error, validation_error
from app.core.errors.codes import ErrorCode
from app.core.logging import logging
from app.core.schemas import PaginationOut
from app.offers.composition import get_offer_service
from app.offers.schemas import OfferOut, PaginatedOffersOut
from app.offers.services import OfferService
from app.users.models import User

router = APIRouter(prefix="/offers", tags=["offers"])

_VALID_OFFER_STATUS_VALUES = {"active", "inactive"}


@router.get(
    "/",
    status_code=status.HTTP_200_OK,
    description=(
        "List all offers with pagination and optional filtering by status,"
        " merchant, or validity date range."
    ),
    responses={
        400: {
            "description": (
                "Invalid query parameters: unrecognised status value"
                " or date_from after date_to."
            ),
            "content": {
                "application/json": {
                    "example": {
                        "error": {
                            "code": "VALIDATION_ERROR",
                            "message": "Invalid query parameters.",
                            "details": {
                                "violations": [
                                    {
                                        "field": "status",
                                        "reason": "Status must be one of: active, inactive.",
                                    }
                                ]
                            },
                        }
                    }
                }
            },
        },
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
            "description": (
                "Request parameter type validation failed"
                " (e.g. non-integer offset, non-UUID merchant_id)."
            ),
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
async def list_offers(
    offset: int = Query(default=0, ge=0, description="Number of results to skip."),
    limit: int = Query(
        default=settings.default_page_size,
        ge=1,
        le=settings.max_page_size,
        description=f"Number of results to return (max {settings.max_page_size}).",
    ),
    status_filter: str | None = Query(
        default=None,
        alias="status",
        description="Filter by offer status: active or inactive.",
    ),
    merchant_id: UUID | None = Query(
        default=None,
        description="Filter offers belonging to a specific merchant.",
    ),
    date_from: date | None = Query(
        default=None,
        description=(
            "Return offers whose validity window ends on or after this date (YYYY-MM-DD)."
        ),
    ),
    date_to: date | None = Query(
        default=None,
        description=(
            "Return offers whose validity window starts on or before this date (YYYY-MM-DD)."
        ),
    ),
    offer_service: OfferService = Depends(get_offer_service),
    db: AsyncSession = Depends(get_async_db),
    _current_user: User = Depends(get_current_user),
) -> PaginatedOffersOut:
    _validate_list_params(status_filter, date_from, date_to)

    try:
        items, total = await offer_service.list_offers(
            offset,
            limit,
            _map_status_to_active(status_filter),
            merchant_id,
            date_from,
            date_to,
            db,
        )
    except Exception as e:
        logging.error(
            "An unexpected error occurred while listing offers.",
            extra={"error": str(e)},
        )
        raise internal_server_error()

    return PaginatedOffersOut(
        data=[OfferOut.model_validate(item) for item in items],
        pagination=PaginationOut(offset=offset, limit=limit, total=total),
    )


def _validate_list_params(
    status_filter: str | None,
    date_from: date | None,
    date_to: date | None,
) -> None:
    violations: list[dict[str, str]] = []
    if status_filter is not None and status_filter not in _VALID_OFFER_STATUS_VALUES:
        violations.append(
            {
                "field": "status",
                "reason": "Status must be one of: active, inactive.",
            }
        )
    if date_from is not None and date_to is not None and date_from > date_to:
        violations.append(
            {
                "field": "date_from",
                "reason": (
                    f"date_from ({date_from}) must not be after date_to ({date_to})."
                ),
            }
        )
    if violations:
        raise validation_error(
            code=ErrorCode.VALIDATION_ERROR,
            message="Invalid query parameters.",
            details=violations,
        )


def _map_status_to_active(status_filter: str | None) -> bool | None:
    if status_filter == "active":
        return True
    elif status_filter == "inactive":
        return False
    return None
