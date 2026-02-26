import pytest

from app.core.config import settings
from app.merchants.exceptions import CashbackPercentageNotValidException
from app.merchants.policies import enforce_cashback_percentage_validity


@pytest.mark.parametrize(
    "percentage",
    [
        0.0,  # lower boundary
        settings.max_cashback_percentage / 2,  # midpoint
        settings.max_cashback_percentage,  # upper boundary
    ],
)
def test_enforce_cashback_percentage_validity_accepts_valid(
    percentage: float,
) -> None:
    # Should not raise
    enforce_cashback_percentage_validity(percentage)


@pytest.mark.parametrize(
    "percentage,expected_message",
    [
        (-0.1, "between 0 and"),
        (-10.0, "between 0 and"),
        (settings.max_cashback_percentage + 0.1, "between 0 and"),
        (150.0, "between 0 and"),
    ],
)
def test_enforce_cashback_percentage_validity_rejects_invalid(
    percentage: float, expected_message: str
) -> None:
    # Act & Assert
    with pytest.raises(CashbackPercentageNotValidException) as exc:
        enforce_cashback_percentage_validity(percentage)
    assert expected_message in str(exc.value)
