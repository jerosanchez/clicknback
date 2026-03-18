from decimal import Decimal
from typing import Any, AsyncGenerator, Generator
from unittest.mock import AsyncMock, Mock, create_autospec

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.core.current_user import get_current_user
from app.core.database import get_async_db
from app.main import app
from app.wallets.composition import get_wallet_service
from app.wallets.schemas import WalletSummaryOut
from app.wallets.services import WalletService

# ──────────────────────────────────────────────────────────────────────────────
# Fixtures
# ──────────────────────────────────────────────────────────────────────────────


@pytest.fixture
def wallet_service_mock() -> Mock:
    return create_autospec(WalletService)


async def _mock_get_async_db() -> AsyncGenerator[AsyncMock, Any]:
    yield AsyncMock()


@pytest.fixture
def client(wallet_service_mock: Mock) -> Generator[TestClient, None, None]:
    app.dependency_overrides[get_async_db] = _mock_get_async_db
    app.dependency_overrides[get_wallet_service] = lambda: wallet_service_mock
    app.dependency_overrides[get_current_user] = lambda: Mock()

    test_client = TestClient(app)
    yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def unauthenticated_client(
    wallet_service_mock: Mock,
) -> Generator[TestClient, None, None]:
    """Client with no auth override — the auth dependency runs normally and rejects the request."""
    app.dependency_overrides[get_async_db] = _mock_get_async_db
    app.dependency_overrides[get_wallet_service] = lambda: wallet_service_mock

    yield TestClient(app, raise_server_exceptions=False)

    app.dependency_overrides.clear()


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────


def _assert_error_payload(data: dict[str, Any], expected_code: str) -> None:
    assert "error" in data
    assert data["error"]["code"] == expected_code


# ──────────────────────────────────────────────────────────────────────────────
# GET /api/v1/users/me/wallet — success
# ──────────────────────────────────────────────────────────────────────────────


def test_get_wallet_summary_returns_200_on_success(
    client: TestClient,
    wallet_service_mock: Mock,
) -> None:
    # Arrange
    expected_pending = Decimal("5.00")
    expected_available = Decimal("25.50")
    expected_paid = Decimal("100.00")
    wallet_service_mock.get_wallet_summary = AsyncMock(
        return_value=WalletSummaryOut(
            pending_balance=expected_pending,
            available_balance=expected_available,
            paid_balance=expected_paid,
        )
    )

    # Act
    response = client.get("/api/v1/users/me/wallet")

    # Assert
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert Decimal(str(data["pending_balance"])) == expected_pending
    assert Decimal(str(data["available_balance"])) == expected_available
    assert Decimal(str(data["paid_balance"])) == expected_paid


# ──────────────────────────────────────────────────────────────────────────────
# GET /api/v1/users/me/wallet — auth failures
# ──────────────────────────────────────────────────────────────────────────────


def test_get_wallet_summary_returns_401_on_unauthenticated(
    unauthenticated_client: TestClient,
) -> None:
    # Act & Assert
    response = unauthenticated_client.get("/api/v1/users/me/wallet")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
