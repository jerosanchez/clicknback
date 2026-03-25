from decimal import Decimal

import pytest

from app.cashback.calculator import CashbackCalculator
from app.cashback.models import CashbackResult


@pytest.fixture
def calculator() -> CashbackCalculator:
    return CashbackCalculator()


# pylint: disable=redefined-outer-name

# ──────────────────────────────────────────────────────────────────────────────
# CashbackCalculator.calculate — percentage-based offers
# ──────────────────────────────────────────────────────────────────────────────


def test_calculate_returns_correct_result_for_percentage_offer(
    calculator: CashbackCalculator,
) -> None:
    # Arrange
    offer_id = "f0e1d2c3-b4a5-4678-9012-3456789abcde"
    percentage = 11.0
    purchase_amount = Decimal("150.00")

    # Act
    result = calculator.calculate(
        offer_id=offer_id,
        percentage=percentage,
        fixed_amount=None,
        purchase_amount=purchase_amount,
    )

    # Assert
    assert result.offer_id == offer_id
    assert result.percentage_applied == percentage
    assert result.fixed_amount_applied is None
    assert result.cashback_amount == Decimal("16.50")


def test_calculate_returns_cashback_result_type_for_percentage_offer(
    calculator: CashbackCalculator,
) -> None:
    # Arrange
    offer_id = "f0e1d2c3-b4a5-4678-9012-3456789abcde"

    # Act
    result = calculator.calculate(
        offer_id=offer_id,
        percentage=5.0,
        fixed_amount=None,
        purchase_amount=Decimal("200.00"),
    )

    # Assert
    assert isinstance(result, CashbackResult)


def test_calculate_rounds_percentage_result_to_two_decimal_places(
    calculator: CashbackCalculator,
) -> None:
    # Arrange — 10 % of 33.33 = 3.333, rounds to 3.33 (banker's rounding)
    purchase_amount = Decimal("33.33")
    percentage = 10.0

    # Act
    result = calculator.calculate(
        offer_id="f0e1d2c3-b4a5-4678-9012-3456789abcde",
        percentage=percentage,
        fixed_amount=None,
        purchase_amount=purchase_amount,
    )

    # Assert
    assert result.cashback_amount == Decimal("3.33")


def test_calculate_handles_fractional_percentage(
    calculator: CashbackCalculator,
) -> None:
    # Arrange — 2.5 % of 200.00 = 5.00
    purchase_amount = Decimal("200.00")
    percentage = 2.5

    # Act
    result = calculator.calculate(
        offer_id="f0e1d2c3-b4a5-4678-9012-3456789abcde",
        percentage=percentage,
        fixed_amount=None,
        purchase_amount=purchase_amount,
    )

    # Assert
    assert result.cashback_amount == Decimal("5.00")


# ──────────────────────────────────────────────────────────────────────────────
# CashbackCalculator.calculate — fixed-amount offers
# ──────────────────────────────────────────────────────────────────────────────


def test_calculate_returns_correct_result_for_fixed_offer(
    calculator: CashbackCalculator,
) -> None:
    # Arrange — fixed offer: €5, regardless of purchase amount
    fixed_reward = 5.0
    large_purchase = Decimal("500.00")

    # Act
    result = calculator.calculate(
        offer_id="f0e1d2c3-b4a5-4678-9012-3456789abcde",
        percentage=10.0,
        fixed_amount=fixed_reward,
        purchase_amount=large_purchase,
    )

    # Assert
    assert result.offer_id == "f0e1d2c3-b4a5-4678-9012-3456789abcde"
    assert result.fixed_amount_applied == fixed_reward
    assert result.percentage_applied is None
    assert result.cashback_amount == Decimal("5.00")


def test_calculate_fixed_takes_precedence_over_percentage(
    calculator: CashbackCalculator,
) -> None:
    # Arrange — both percentage and fixed supplied; fixed must win
    percentage_reward_would_be = Decimal("100.00") * Decimal("10") / Decimal("100")
    fixed_reward = 3.0

    # Act
    result = calculator.calculate(
        offer_id="f0e1d2c3-b4a5-4678-9012-3456789abcde",
        percentage=10.0,
        fixed_amount=fixed_reward,
        purchase_amount=Decimal("100.00"),
    )

    # Assert
    assert result.cashback_amount != percentage_reward_would_be
    assert result.cashback_amount == Decimal("3.00")


def test_calculate_rounds_fixed_amount_to_two_decimal_places(
    calculator: CashbackCalculator,
) -> None:
    # Arrange — fixed amount with more than 2 decimal places in float representation
    fixed_reward = 2.505

    # Act
    result = calculator.calculate(
        offer_id="f0e1d2c3-b4a5-4678-9012-3456789abcde",
        percentage=0.0,
        fixed_amount=fixed_reward,
        purchase_amount=Decimal("100.00"),
    )

    # Assert
    assert result.cashback_amount.as_tuple().exponent == -2


# ──────────────────────────────────────────────────────────────────────────────
# CashbackCalculator.calculate — edge cases
# ──────────────────────────────────────────────────────────────────────────────


def test_calculate_returns_zero_for_zero_percentage(
    calculator: CashbackCalculator,
) -> None:
    # Arrange
    purchase_amount = Decimal("100.00")

    # Act
    result = calculator.calculate(
        offer_id="f0e1d2c3-b4a5-4678-9012-3456789abcde",
        percentage=0.0,
        fixed_amount=None,
        purchase_amount=purchase_amount,
    )

    # Assert
    assert result.cashback_amount == Decimal("0.00")


def test_calculate_returns_zero_for_zero_purchase_amount(
    calculator: CashbackCalculator,
) -> None:
    # Arrange
    zero_purchase = Decimal("0.00")

    # Act
    result = calculator.calculate(
        offer_id="f0e1d2c3-b4a5-4678-9012-3456789abcde",
        percentage=10.0,
        fixed_amount=None,
        purchase_amount=zero_purchase,
    )

    # Assert
    assert result.cashback_amount == Decimal("0.00")
