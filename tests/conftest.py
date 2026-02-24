from typing import Any, Callable

import pytest

from app.users.models import User

default_user_factory_defaults: dict[str, Any] = {
    "id": "b7e2c1a2-4f3a-4e2b-9c1a-8d2e3f4b5c6d",
    "email": "alice@example.com",
    "hashed_password": "hashed_pw",
    "role": "admin",
    "active": True,
    "created_at": "2026-02-15T18:42:18.340977",
}


@pytest.fixture
def user_factory() -> Callable[..., User]:
    def _make_user(**kwargs: Any) -> User:
        defaults = dict(default_user_factory_defaults)
        defaults.update(kwargs)
        return User(**defaults)

    return _make_user
