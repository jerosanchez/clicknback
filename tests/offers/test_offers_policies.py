from datetime import date

import pytest

from app.core.config import settings
from app.offers.exceptions import (
    ActiveOfferAlreadyExistsException,
    InvalidCashbackValueException,
    InvalidDateRangeException,
    InvalidMonthlyCapException,
    MerchantNotActiveException,
    PastOfferStartDateException,
)
from app.offers.policies import (
    enforce_cashback_value_validity,
    enforce_date_range_validity,
    enforce_merchant_is_active,
    enforce_monthly_cap_validity,
    enforce_no_active_offer_exists,
)
from app.offers.schemas import CashbackTypeEnum

MERCHANT_ID = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"


# ──────────────────────────────────────────────────────────────────────────────
# enforce_cashback_value_validity
# ──────────────────────────────────────────────────────────────────────────────


@pytest.mark.parametrize("value", [0.1, 5.0, 10.0, settings.max_cashback_percentage])
def test_enforce_cashback_value_validity_raises_nothing_on_valid_percent(
    value: float,
) -> None:
    # Act & Assert
    enforce_cashback_value_validity(CashbackTypeEnum.percent, value)


@pytest.mark.parametrize("value", [0.01, 1.00, 100.00])
def test_enforce_cashback_value_validity_raises_nothing_on_valid_fixed(
    value: float,
) -> None:
    # Act & Assert
    enforce_cashback_value_validity(CashbackTypeEnum.fixed, value)


@pytest.mark.parametrize("value", [0.0, -1.0, settings.max_cashback_percentage + 0.01])
def test_enforce_cashback_value_validity_raises_on_invalid_percent(
    value: float,
) -> None:
    # Act & Assert
    with pytest.raises(InvalidCashbackValueException) as exc_info:
        enforce_cashback_value_validity(CashbackTypeEnum.percent, value)
    assert exc_info.value.cashback_type == CashbackTypeEnum.percent
    assert exc_info.value.value == value


@pytest.mark.parametrize("value", [0.0, -5.0])
def test_enforce_cashback_value_validity_raises_on_invalid_fixed(
    value: float,
) -> None:
    # Act & Assert
    with pytest.raises(InvalidCashbackValueException) as exc_info:
        enforce_cashback_value_validity(CashbackTypeEnum.fixed, value)
    assert exc_info.value.cashback_type == CashbackTypeEnum.fixed
    assert exc_info.value.value == value


# ──────────────────────────────────────────────────────────────────────────────
# enforce_date_range_validity
# ──────────────────────────────────────────────────────────────────────────────


def test_enforce_date_range_validity_raises_nothing_on_same_day() -> None:
    same_day = date(2026, 6, 1)
    # Act & Assert
    enforce_date_range_validity(same_day, same_day)


def test_enforce_date_range_validity_raises_nothing_on_valid_range() -> None:
    # Arrange
    start_date = date(2026, 6, 1)
    end_date = date(2026, 12, 31)

    # Act & Assert
    enforce_date_range_validity(start_date, end_date)


def test_enforce_date_range_validity_raises_on_end_before_start() -> None:
    # Arrange
    start_date = date(2026, 12, 31)
    end_before_start_date = date(2026, 6, 1)

    # Act & Assert
    with pytest.raises(InvalidDateRangeException) as exc_info:
        enforce_date_range_validity(start_date, end_before_start_date)
    assert exc_info.value.start_date == start_date
    assert exc_info.value.end_date == end_before_start_date


def test_enforce_date_range_validity_raises_on_past_start_date() -> None:
    # Arrange
    past_start_date = date(2025, 1, 1)  # Past date
    end_date = date(2026, 12, 31)

    # Act & Assert
    with pytest.raises(PastOfferStartDateException) as exc_info:
        enforce_date_range_validity(past_start_date, end_date)
    assert exc_info.value.start_date == past_start_date


# ──────────────────────────────────────────────────────────────────────────────
# enforce_monthly_cap_validity
# ──────────────────────────────────────────────────────────────────────────────


@pytest.mark.parametrize("value", [0.01, 1.0, 50.0, 10_000.0])
def test_enforce_monthly_cap_validity_raises_nothing_on_valid_cap(
    value: float,
) -> None:
    # Act & Assert
    enforce_monthly_cap_validity(value)


@pytest.mark.parametrize("value", [0.0, -1.0, -100.0])
def test_enforce_monthly_cap_validity_raises_on_non_positive_cap(
    value: float,
) -> None:
    # Act & Assert
    with pytest.raises(InvalidMonthlyCapException) as exc_info:
        enforce_monthly_cap_validity(value)
    assert exc_info.value.value == value


# ──────────────────────────────────────────────────────────────────────────────
# enforce_merchant_is_active
# ──────────────────────────────────────────────────────────────────────────────


def test_enforce_merchant_is_active_raises_nothing_on_active_merchant() -> None:
    # Act & Assert
    enforce_merchant_is_active(MERCHANT_ID, is_active=True)


def test_enforce_merchant_is_active_raises_on_inactive_merchant() -> None:
    # Act & Assert
    with pytest.raises(MerchantNotActiveException) as exc_info:
        enforce_merchant_is_active(MERCHANT_ID, is_active=False)
    assert exc_info.value.merchant_id == MERCHANT_ID


# ──────────────────────────────────────────────────────────────────────────────
# enforce_no_active_offer_exists
# ──────────────────────────────────────────────────────────────────────────────


def test_enforce_no_active_offer_exists_raises_nothing_when_no_active_offer() -> None:
    # Act & Assert
    enforce_no_active_offer_exists(MERCHANT_ID, has_active_offer=False)


def test_enforce_no_active_offer_exists_raises_on_existing_active_offer() -> None:
    # Act & Assert
    with pytest.raises(ActiveOfferAlreadyExistsException) as exc_info:
        enforce_no_active_offer_exists(MERCHANT_ID, has_active_offer=True)
    assert exc_info.value.merchant_id == MERCHANT_ID
