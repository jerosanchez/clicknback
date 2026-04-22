from typing import Any, AsyncGenerator, Generator
from unittest.mock import AsyncMock, Mock, create_autospec

import pytest
from fastapi.testclient import TestClient

from app.auth.exceptions import InvalidTokenException
from app.core.current_user import get_current_admin_user, get_current_user
from app.core.database import get_async_db
from app.core.errors.builders import forbidden_error
from app.main import app
from app.offers.composition import get_offer_service
from app.offers.services import OfferService
from app.users.models import UserRoleEnum


@pytest.fixture
def offer_service_mock() -> Mock:
    return create_autospec(OfferService)


async def _mock_get_async_db() -> AsyncGenerator[AsyncMock, Any]:
    yield AsyncMock()


@pytest.fixture
def admin_api_client(offer_service_mock: Mock) -> Generator[TestClient, None, None]:
    """Authenticated admin client for admin-only endpoints."""
    app.dependency_overrides[get_async_db] = _mock_get_async_db
    app.dependency_overrides[get_offer_service] = lambda: offer_service_mock
    app.dependency_overrides[get_current_admin_user] = lambda: Mock()

    yield TestClient(app)

    app.dependency_overrides.clear()


@pytest.fixture
def non_admin_client(offer_service_mock: Mock) -> Generator[TestClient, None, None]:
    """Client that triggers a 403 on admin-only endpoints."""

    def raise_forbidden() -> None:
        raise forbidden_error("Admin access required.", {})

    app.dependency_overrides[get_async_db] = _mock_get_async_db
    app.dependency_overrides[get_offer_service] = lambda: offer_service_mock
    app.dependency_overrides[get_current_admin_user] = raise_forbidden

    yield TestClient(app)

    app.dependency_overrides.clear()


@pytest.fixture
def user_client(offer_service_mock: Mock) -> Generator[TestClient, None, None]:
    """Authenticated regular-user client for public endpoints."""
    app.dependency_overrides[get_async_db] = _mock_get_async_db
    app.dependency_overrides[get_offer_service] = lambda: offer_service_mock
    app.dependency_overrides[get_current_user] = lambda: Mock(role=UserRoleEnum.user)

    yield TestClient(app)

    app.dependency_overrides.clear()


@pytest.fixture
def admin_user_client(offer_service_mock: Mock) -> Generator[TestClient, None, None]:
    """Authenticated admin client for public endpoints (role-sensitive behaviour)."""
    app.dependency_overrides[get_async_db] = _mock_get_async_db
    app.dependency_overrides[get_offer_service] = lambda: offer_service_mock
    app.dependency_overrides[get_current_user] = lambda: Mock(role=UserRoleEnum.admin)

    yield TestClient(app)

    app.dependency_overrides.clear()


@pytest.fixture
def unauthenticated_client(
    offer_service_mock: Mock,
) -> Generator[TestClient, None, None]:
    """Client that triggers a 401 on authenticated endpoints."""

    def raise_invalid_token() -> None:
        raise InvalidTokenException()

    app.dependency_overrides[get_async_db] = _mock_get_async_db
    app.dependency_overrides[get_offer_service] = lambda: offer_service_mock
    app.dependency_overrides[get_current_user] = raise_invalid_token

    yield TestClient(app)

    app.dependency_overrides.clear()


def assert_error_code(data: dict[str, Any], expected_code: str) -> None:
    assert "error" in data
    assert data["error"]["code"] == expected_code
