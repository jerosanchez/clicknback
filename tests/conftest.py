from datetime import date
from decimal import Decimal
from typing import Any, Callable

import pytest

from app.merchants.models import Merchant
from app.offers.models import Offer
from app.purchases.models import Purchase
from app.users.models import User


@pytest.fixture
def user_factory() -> Callable[..., User]:
    def _make_user(**kwargs: Any) -> User:
        defaults: dict[str, Any] = {
            "id": "b7e2c1a2-4f3a-4e2b-9c1a-8d2e3f4b5c6d",
            "email": "alice@example.com",
            "hashed_password": "hashed_pw",
            "role": "admin",
            "active": True,
            "created_at": "2026-02-15T18:42:18.340977",
        }
        defaults.update(kwargs)
        return User(**defaults)

    return _make_user


@pytest.fixture
def user_input_data() -> Callable[[User], dict[str, Any]]:
    def _build(user: User) -> dict[str, Any]:
        return {
            "email": user.email,
            "password": "PlaceholderPass1!",
        }

    return _build


@pytest.fixture
def merchant_factory() -> Callable[..., Merchant]:
    def _make_merchant(**kwargs: Any) -> Merchant:
        defaults: dict[str, Any] = {
            "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
            "name": "Acme Corp",
            "default_cashback_percentage": 5.0,
            "active": True,
        }
        defaults.update(kwargs)
        return Merchant(**defaults)

    return _make_merchant


@pytest.fixture
def merchant_input_data() -> Callable[[Merchant], dict[str, Any]]:
    def _build(merchant: Merchant) -> dict[str, Any]:
        return {
            "name": merchant.name,
            "default_cashback_percentage": merchant.default_cashback_percentage,
            "active": merchant.active,
        }

    return _build


@pytest.fixture
def offer_factory() -> Callable[..., Offer]:
    def _make_offer(**kwargs: Any) -> Offer:
        defaults: dict[str, Any] = {
            "id": "f0e1d2c3-b4a5-4678-9012-3456789abcde",
            "merchant_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
            "percentage": 10.0,
            "fixed_amount": None,
            "start_date": date(2026, 3, 1),
            "end_date": date(2026, 12, 31),
            "monthly_cap_per_user": 50.0,
            "active": True,
        }
        defaults.update(kwargs)
        return Offer(**defaults)

    return _make_offer


@pytest.fixture
def offer_input_data() -> Callable[[Offer], dict[str, Any]]:
    def _build(offer: Offer) -> dict[str, Any]:
        cashback_type = "fixed" if offer.fixed_amount is not None else "percent"
        cashback_value = (
            offer.fixed_amount if offer.fixed_amount is not None else offer.percentage
        )
        return {
            "merchant_id": offer.merchant_id,
            "cashback_type": cashback_type,
            "cashback_value": cashback_value,
            "start_date": offer.start_date.isoformat(),
            "end_date": offer.end_date.isoformat(),
            "monthly_cap": offer.monthly_cap_per_user,
        }

    return _build


@pytest.fixture
def purchase_factory() -> Callable[..., Purchase]:
    def _make_purchase(**kwargs: Any) -> Purchase:
        defaults: dict[str, Any] = {
            "id": "aa000001-0000-0000-0000-000000000001",
            "external_id": "txn_test_001",
            "user_id": "b7e2c1a2-4f3a-4e2b-9c1a-8d2e3f4b5c6d",
            "merchant_id": "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d",
            "offer_id": "f0e1d2c3-b4a5-4678-9012-3456789abcde",
            "amount": Decimal("100.00"),
            "cashback_amount": Decimal("0"),
            "currency": "EUR",
            "status": "pending",
            "created_at": "2026-03-01T10:00:00",
        }
        defaults.update(kwargs)
        return Purchase(**defaults)

    return _make_purchase


@pytest.fixture
def purchase_input_data() -> Callable[[Purchase], dict[str, Any]]:
    def _build(purchase: Purchase) -> dict[str, Any]:
        return {
            "external_id": purchase.external_id,
            "user_id": purchase.user_id,
            "merchant_id": purchase.merchant_id,
            "amount": str(purchase.amount),
            "currency": purchase.currency,
        }

    return _build
