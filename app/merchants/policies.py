from app.core.config import settings
from app.merchants.exceptions import CashbackPercentageNotValidException


def enforce_cashback_percentage_validity(percentage: float) -> None:
    max_percentage = settings.max_cashback_percentage
    if not (0 <= percentage <= max_percentage):
        raise CashbackPercentageNotValidException(
            f"Default cashback percentage must be between 0 and {max_percentage}."
        )
