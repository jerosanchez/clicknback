from typing import Any, Callable

import pytest

from app.merchants.models import Merchant
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
