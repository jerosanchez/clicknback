from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.current_user import get_current_admin_user
from app.core.database import get_db
from app.core.errors.builders import (
    business_rule_violation_error,
    internal_server_error,
    not_found_error,
    unprocessable_entity_error,
    validation_error,
)
from app.core.errors.codes import ErrorCode
from app.core.logging import logging
from app.merchants.exceptions import MerchantNotFoundException
from app.offers.composition import get_offer_service
from app.offers.errors import ErrorCode as OfferErrorCode
from app.offers.exceptions import (
    ActiveOfferAlreadyExistsException,
    InvalidCashbackValueException,
    InvalidDateRangeException,
    InvalidMonthlyCapException,
    MerchantNotActiveException,
    OfferNotFoundException,
    PastOfferStartDateException,
)
from app.offers.schemas import (
    OfferCreate,
    OfferOut,
    OfferStatusEnum,
    OfferStatusOut,
    OfferStatusUpdate,
    PaginatedOffersOut,
)
from app.offers.services import OfferService
from app.users.models import User

router = APIRouter(prefix="/offers", tags=["offers"])


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    description="Create a new offer for a merchant.",
)
def create_offer(
    create_data: OfferCreate,
    offer_service: OfferService = Depends(get_offer_service),
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_admin_user),
) -> OfferOut:
    try:
        new_offer = offer_service.create_offer(create_data.model_dump(), db)

    except InvalidCashbackValueException as exc:
        logging.debug(
            "Offer creation failed: invalid cashback value.",
            extra={"error": str(exc)},
        )
        raise validation_error(
            code=ErrorCode.VALIDATION_ERROR,
            message="Validation failed for request body.",
            details=[{"field": "cashback_value", "reason": exc.reason}],
        )

    except PastOfferStartDateException as exc:
        logging.debug(
            "Offer creation failed: start date is in the past.",
            extra={"error": str(exc)},
        )
        raise validation_error(
            code=ErrorCode.VALIDATION_ERROR,
            message="Validation failed for request body.",
            details=[
                {
                    "field": "start_date",
                    "reason": (
                        f"Start date must be today or a future date."
                        f" Got: '{exc.start_date}'."
                    ),
                }
            ],
        )

    except InvalidDateRangeException as exc:
        logging.debug(
            "Offer creation failed: invalid date range.",
            extra={"error": str(exc)},
        )
        raise validation_error(
            code=ErrorCode.VALIDATION_ERROR,
            message="Validation failed for request body.",
            details=[
                {
                    "field": "end_date",
                    "reason": (
                        f"End date must be after start date."
                        f" Got start='{exc.start_date}', end='{exc.end_date}'."
                    ),
                }
            ],
        )

    except InvalidMonthlyCapException as exc:
        logging.debug(
            "Offer creation failed: invalid monthly cap.",
            extra={"error": str(exc)},
        )
        raise validation_error(
            code=ErrorCode.VALIDATION_ERROR,
            message="Validation failed for request body.",
            details=[
                {
                    "field": "monthly_cap",
                    "reason": f"Monthly cap must be positive. Got: {exc.value}.",
                }
            ],
        )

    except MerchantNotFoundException as exc:
        raise not_found_error(
            message=str(exc),
            details={
                "resource_type": "merchant",
                "resource_id": exc.merchant_id,
            },
        )

    except MerchantNotActiveException as exc:
        raise unprocessable_entity_error(
            code=OfferErrorCode.MERCHANT_NOT_ACTIVE,
            message=str(exc),
            details={
                "merchant_id": exc.merchant_id,
                "action": "Activate the merchant before creating offers.",
            },
        )

    except ActiveOfferAlreadyExistsException as exc:
        raise business_rule_violation_error(
            code=OfferErrorCode.ACTIVE_OFFER_ALREADY_EXISTS,
            message=str(exc),
            details={
                "merchant_id": exc.merchant_id,
                "action": "Deactivate the existing offer before creating a new one.",
            },
        )

    except Exception as e:
        logging.error(
            "An unexpected error occurred while creating an offer.",
            extra={"error": str(e)},
        )
        raise internal_server_error()

    return OfferOut.model_validate(new_offer)


_VALID_OFFER_STATUS_VALUES = {"active", "inactive"}


@router.get(
    "/",
    status_code=status.HTTP_200_OK,
    description=(
        "List all offers with pagination and optional filtering by status,"
        " merchant, or validity date range."
    ),
)
def list_offers(
    page: int = Query(default=1, ge=1, description="Page number (1-indexed)."),
    page_size: int = Query(
        default=settings.default_page_size,
        ge=1,
        le=settings.max_page_size,
        description=f"Number of results per page (max {settings.max_page_size}).",
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
        description="Return offers whose validity window ends on or after this date (YYYY-MM-DD).",
    ),
    date_to: date | None = Query(
        default=None,
        description="Return offers whose validity window starts on or before this date (YYYY-MM-DD).",
    ),
    offer_service: OfferService = Depends(get_offer_service),
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_admin_user),
) -> PaginatedOffersOut:
    _validate_offer_query_params(status_filter, date_from, date_to)

    try:
        items, total = offer_service.list_offers(
            page,
            page_size,
            _map_to_active(status_filter),
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
        items=[OfferOut.model_validate(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
    )


def _validate_offer_query_params(
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
                "reason": f"date_from ({date_from}) must not be after date_to ({date_to}).",
            }
        )
    if violations:
        raise validation_error(
            code=ErrorCode.VALIDATION_ERROR,
            message="Invalid query parameters.",
            details=violations,
        )


def _map_to_active(status_filter: str | None) -> bool | None:
    if status_filter == "active":
        return True
    elif status_filter == "inactive":
        return False
    else:
        return None


@router.patch(
    "/{offer_id}/status",
    status_code=status.HTTP_200_OK,
    description="Activate or deactivate an offer.",
)
def set_offer_status(
    offer_id: str,
    update_data: OfferStatusUpdate,
    offer_service: OfferService = Depends(get_offer_service),
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_admin_user),
) -> OfferStatusOut:
    active = update_data.status == "active"
    try:
        updated = offer_service.set_offer_status(offer_id, active, db)

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
