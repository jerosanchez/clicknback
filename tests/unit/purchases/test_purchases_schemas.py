from decimal import Decimal
from typing import Any

import pytest
from pydantic import ValidationError

from app.purchases.schemas import PurchaseCreate


def _valid_payload(**overrides: Any) -> dict[str, Any]:
    base: dict[str, Any] = {
        "external_id": "txn-001",
        "user_id": "b7e2c1a2-4f3a-4e2b-9c1a-8d2e3f4b5c6d",
        "merchant_id": "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d",
        "amount": "100.00",
        "currency": "EUR",
    }
    base.update(overrides)
    return base


# ──────────────────────────────────────────────────────────────────────────────
# amount scale validator
# ──────────────────────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "amount",
    [
        "1",  # integer — 0 decimal places
        "10.5",  # 1 decimal place
        "100.00",  # 2 decimal places — upper scale boundary
        "0.01",  # minimum positive with 2 decimal places
        "9999999999.99",  # maximum representable value at precision=12, scale=2
    ],
)
def test_purchase_create_accepts_valid_amount_scale(amount: str) -> None:
    # Act — should not raise
    schema = PurchaseCreate(**_valid_payload(amount=amount))

    # Assert
    assert schema.amount == Decimal(amount)


@pytest.mark.parametrize(
    "amount,expected_message",
    [
        ("100.001", "at most 2 decimal places"),  # 3 decimal places
        ("0.001", "at most 2 decimal places"),  # 3 decimal places — near zero
        ("1.1234", "at most 2 decimal places"),  # 4 decimal places
    ],
)
def test_purchase_create_rejects_amount_with_excess_scale(
    amount: str, expected_message: str
) -> None:
    # Act & Assert
    with pytest.raises(ValidationError) as exc_info:
        PurchaseCreate(**_valid_payload(amount=amount))
    assert expected_message in str(exc_info.value)
