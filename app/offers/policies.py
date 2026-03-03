from datetime import date

from app.core.config import settings
from app.offers.exceptions import (
    ActiveOfferAlreadyExistsException,
    InvalidCashbackValueException,
    InvalidDateRangeException,
    InvalidMonthlyCapException,
    MerchantNotActiveException,
    PastOfferStartDateException,
)
from app.offers.schemas import CashbackTypeEnum


def enforce_cashback_value_validity(
    cashback_type: CashbackTypeEnum, cashback_value: float
) -> None:
    if cashback_type == CashbackTypeEnum.percent:
        if not (0 < cashback_value <= settings.max_cashback_percentage):
            raise InvalidCashbackValueException(
                cashback_type.value,
                cashback_value,
                f"Percentage must be between 0 (exclusive) and {settings.max_cashback_percentage} (inclusive).",
            )
    elif cashback_type == CashbackTypeEnum.fixed:
        if cashback_value <= 0:
            raise InvalidCashbackValueException(
                cashback_type.value,
                cashback_value,
                "Fixed amount must be greater than 0.",
            )


def enforce_date_range_validity(start_date: date, end_date: date) -> None:
    if start_date < date.today():
        raise PastOfferStartDateException(start_date)

    if end_date < start_date:
        raise InvalidDateRangeException(start_date, end_date)


def enforce_monthly_cap_validity(monthly_cap: float) -> None:
    if monthly_cap <= 0:
        raise InvalidMonthlyCapException(monthly_cap)


def enforce_merchant_is_active(merchant_id: str, is_active: bool) -> None:
    if not is_active:
        raise MerchantNotActiveException(merchant_id)


def enforce_no_active_offer_exists(merchant_id: str, has_active_offer: bool) -> None:
    if has_active_offer:
        raise ActiveOfferAlreadyExistsException(merchant_id)
