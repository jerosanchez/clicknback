from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

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
    PastOfferStartDateException,
)
from app.offers.schemas import OfferCreate, OfferOut
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
