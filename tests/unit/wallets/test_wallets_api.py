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
from app.wallets.schemas import (
    PaginatedWalletTransactionOut,
    WalletSummaryOut,
    WalletTransactionOut,
    WalletTransactionType,
)
from app.wallets.services import WalletService

# ──────────────────────────────────────────────────────────────────────────────
# Fixtures
# ──────────────────────────────────────────────────────────────────────────────

_USER_ID = "b7e2c1a2-4f3a-4e2b-9c1a-8d2e3f4b5c6d"
_TXN_ID = "ct000001-0000-0000-0000-000000000001"
_PURCHASE_ID = "aa000001-0000-0000-0000-000000000001"


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


def _make_transaction_out(
    txn_id: str = _TXN_ID,
    txn_type: WalletTransactionType = WalletTransactionType.CASHBACK_CREDIT,
    amount: Decimal = Decimal("5.00"),
    txn_status: str = "available",
    purchase_id: str = _PURCHASE_ID,
) -> WalletTransactionOut:
    return WalletTransactionOut(
        id=txn_id,
        type=txn_type,
        amount=amount,
        status=txn_status,
        related_purchase_id=purchase_id,
    )


def _assert_transaction_response(
    data: dict[str, Any], txn: WalletTransactionOut
) -> None:
    assert data["id"] == txn.id
    assert data["type"] == txn.type.value
    assert Decimal(str(data["amount"])) == txn.amount
    assert data["status"] == txn.status
    assert data["related_purchase_id"] == txn.related_purchase_id


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


# ──────────────────────────────────────────────────────────────────────────────
# GET /api/v1/users/me/wallet/transactions — success
# ──────────────────────────────────────────────────────────────────────────────


def test_list_wallet_transactions_returns_200_on_success(
    client: TestClient,
    wallet_service_mock: Mock,
) -> None:
    # Arrange
    txn = _make_transaction_out()
    wallet_service_mock.list_wallet_transactions = AsyncMock(
        return_value=PaginatedWalletTransactionOut(transactions=[txn], total=1)
    )

    # Act
    response = client.get("/api/v1/users/me/wallet/transactions")

    # Assert
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["total"] == 1
    assert len(data["transactions"]) == 1
    _assert_transaction_response(data["transactions"][0], txn)


def test_list_wallet_transactions_returns_200_on_empty_list(
    client: TestClient,
    wallet_service_mock: Mock,
) -> None:
    # Arrange
    wallet_service_mock.list_wallet_transactions = AsyncMock(
        return_value=PaginatedWalletTransactionOut(transactions=[], total=0)
    )

    # Act
    response = client.get("/api/v1/users/me/wallet/transactions")

    # Assert
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["total"] == 0
    assert data["transactions"] == []


def test_list_wallet_transactions_forwards_limit_and_offset_to_service(
    client: TestClient,
    wallet_service_mock: Mock,
) -> None:
    # Arrange
    wallet_service_mock.list_wallet_transactions = AsyncMock(
        return_value=PaginatedWalletTransactionOut(transactions=[], total=0)
    )

    # Act
    client.get("/api/v1/users/me/wallet/transactions?limit=20&offset=40")

    # Assert
    call_kwargs = wallet_service_mock.list_wallet_transactions.call_args
    assert call_kwargs.args[1] == 20  # limit
    assert call_kwargs.args[2] == 40  # offset


def test_list_wallet_transactions_returns_cashback_credit_type_on_reversed_status(
    client: TestClient,
    wallet_service_mock: Mock,
) -> None:
    # Arrange — a reversed cashback is still type=cashback_credit; status carries the state
    txn = _make_transaction_out(
        txn_type=WalletTransactionType.CASHBACK_CREDIT, txn_status="reversed"
    )
    wallet_service_mock.list_wallet_transactions = AsyncMock(
        return_value=PaginatedWalletTransactionOut(transactions=[txn], total=1)
    )

    # Act
    response = client.get("/api/v1/users/me/wallet/transactions")

    # Assert
    data = response.json()
    assert data["transactions"][0]["type"] == "cashback_credit"
    assert data["transactions"][0]["status"] == "reversed"


# ──────────────────────────────────────────────────────────────────────────────
# GET /api/v1/users/me/wallet/transactions — 500
# ──────────────────────────────────────────────────────────────────────────────


def test_list_wallet_transactions_returns_500_on_unexpected_error(
    client: TestClient,
    wallet_service_mock: Mock,
) -> None:
    # Arrange
    wallet_service_mock.list_wallet_transactions = AsyncMock(
        side_effect=RuntimeError("database exploded")
    )

    # Act
    response = client.get("/api/v1/users/me/wallet/transactions")

    # Assert
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    _assert_error_payload(response.json(), "INTERNAL_SERVER_ERROR")


# ──────────────────────────────────────────────────────────────────────────────
# GET /api/v1/users/me/wallet/transactions — auth failures
# ──────────────────────────────────────────────────────────────────────────────


def test_list_wallet_transactions_returns_401_on_unauthenticated(
    unauthenticated_client: TestClient,
) -> None:
    # Act & Assert
    response = unauthenticated_client.get("/api/v1/users/me/wallet/transactions")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


# ──────────────────────────────────────────────────────────────────────────────
# GET /api/v1/users/me/wallet/transactions — pagination param validation
# ──────────────────────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "query_string",
    [
        "limit=0",  # below minimum limit
        "limit=101",  # above maximum limit
        "offset=-1",  # below minimum offset
    ],
)
def test_list_wallet_transactions_returns_422_on_invalid_pagination_params(
    client: TestClient,
    query_string: str,
) -> None:
    # Act
    response = client.get(f"/api/v1/users/me/wallet/transactions?{query_string}")

    # Assert
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
