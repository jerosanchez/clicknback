from datetime import datetime
from decimal import Decimal
from unittest.mock import AsyncMock, Mock, create_autospec

import pytest

from app.wallets.clients.cashback import CashbackClientABC, CashbackTransactionDTO
from app.wallets.models import Wallet
from app.wallets.repositories import WalletRepositoryABC
from app.wallets.schemas import (
    PaginatedWalletTransactionOut,
    WalletSummaryOut,
    WalletTransactionType,
)
from app.wallets.services import WalletService

# ──────────────────────────────────────────────────────────────────────────────
# Fixtures
# ──────────────────────────────────────────────────────────────────────────────

_USER_ID = "b7e2c1a2-4f3a-4e2b-9c1a-8d2e3f4b5c6d"
_PURCHASE_ID = "aa000001-0000-0000-0000-000000000001"
_TXN_ID = "ct000001-0000-0000-0000-000000000001"


@pytest.fixture
def wallet_repository() -> Mock:
    return create_autospec(WalletRepositoryABC)


@pytest.fixture
def cashback_client() -> Mock:
    return create_autospec(CashbackClientABC)


@pytest.fixture
def wallet_service(wallet_repository: Mock, cashback_client: Mock) -> WalletService:
    return WalletService(repository=wallet_repository, cashback_client=cashback_client)


def _make_wallet(**overrides: object) -> Wallet:
    wallet = Wallet()
    wallet.user_id = _USER_ID
    wallet.pending_balance = Decimal("5.00")
    wallet.available_balance = Decimal("25.50")
    wallet.paid_balance = Decimal("100.00")
    for key, value in overrides.items():
        setattr(wallet, key, value)
    return wallet


def _make_cashback_txn(
    status: str = "available",
    amount: Decimal = Decimal("5.00"),
    txn_id: str = _TXN_ID,
    purchase_id: str = _PURCHASE_ID,
) -> CashbackTransactionDTO:
    return CashbackTransactionDTO(
        id=txn_id,
        purchase_id=purchase_id,
        amount=amount,
        status=status,
        created_at=datetime(2026, 3, 10, 12, 0, 0),
    )


# ──────────────────────────────────────────────────────────────────────────────
# WalletService.get_wallet_summary — happy path
# ──────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_wallet_summary_returns_balances_on_existing_wallet(
    wallet_service: WalletService,
    wallet_repository: Mock,
) -> None:
    # Arrange
    wallet = _make_wallet()
    wallet_repository.get_by_user_id = AsyncMock(return_value=wallet)
    db = AsyncMock()

    # Act
    result = await wallet_service.get_wallet_summary(_USER_ID, db)

    # Assert
    assert isinstance(result, WalletSummaryOut)
    assert result.pending_balance == Decimal("5.00")
    assert result.available_balance == Decimal("25.50")
    assert result.paid_balance == Decimal("100.00")


# ──────────────────────────────────────────────────────────────────────────────
# WalletService.get_wallet_summary — new user with no cashback activity
# ──────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_wallet_summary_returns_zeros_on_no_wallet(
    wallet_service: WalletService,
    wallet_repository: Mock,
) -> None:
    # Arrange
    wallet_repository.get_by_user_id = AsyncMock(return_value=None)
    db = AsyncMock()

    # Act
    result = await wallet_service.get_wallet_summary(_USER_ID, db)

    # Assert
    assert isinstance(result, WalletSummaryOut)
    assert result.pending_balance == Decimal("0")
    assert result.available_balance == Decimal("0")
    assert result.paid_balance == Decimal("0")


# ──────────────────────────────────────────────────────────────────────────────
# WalletService.list_wallet_transactions — happy path
# ──────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_list_wallet_transactions_returns_paginated_result_on_success(
    wallet_service: WalletService,
    cashback_client: Mock,
) -> None:
    # Arrange
    txn = _make_cashback_txn(status="available", amount=Decimal("5.00"))
    cashback_client.list_by_user_id = AsyncMock(return_value=([txn], 1))
    db = AsyncMock()

    # Act
    result = await wallet_service.list_wallet_transactions(_USER_ID, 10, 0, db)

    # Assert
    assert isinstance(result, PaginatedWalletTransactionOut)
    assert result.total == 1
    assert len(result.transactions) == 1
    item = result.transactions[0]
    assert item.id == _TXN_ID
    assert item.type == WalletTransactionType.CASHBACK_CREDIT
    assert item.amount == Decimal("5.00")
    assert item.status == "available"
    assert item.related_purchase_id == _PURCHASE_ID


@pytest.mark.asyncio
async def test_list_wallet_transactions_forwards_limit_and_offset_to_client(
    wallet_service: WalletService,
    cashback_client: Mock,
) -> None:
    # Arrange
    cashback_client.list_by_user_id = AsyncMock(return_value=([], 0))
    db = AsyncMock()

    # Act
    await wallet_service.list_wallet_transactions(_USER_ID, 25, 50, db)

    # Assert
    cashback_client.list_by_user_id.assert_called_once_with(db, _USER_ID, 25, 50)


# ──────────────────────────────────────────────────────────────────────────────
# WalletService.list_wallet_transactions — empty list
# ──────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_list_wallet_transactions_returns_empty_list_when_no_transactions(
    wallet_service: WalletService,
    cashback_client: Mock,
) -> None:
    # Arrange
    cashback_client.list_by_user_id = AsyncMock(return_value=([], 0))
    db = AsyncMock()

    # Act
    result = await wallet_service.list_wallet_transactions(_USER_ID, 10, 0, db)

    # Assert
    assert result.total == 0
    assert result.transactions == []


# ──────────────────────────────────────────────────────────────────────────────
# WalletService.list_wallet_transactions — type is always cashback_credit
# ──────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "cashback_status",
    [
        "pending",  # awaiting confirmation
        "available",  # confirmed; in spendable balance
        "reversed",  # purchase reversed; cashback clawed back
    ],
)
async def test_list_wallet_transactions_type_is_always_cashback_credit(
    wallet_service: WalletService,
    cashback_client: Mock,
    cashback_status: str,
) -> None:
    # Arrange
    txn = _make_cashback_txn(status=cashback_status)
    cashback_client.list_by_user_id = AsyncMock(return_value=([txn], 1))
    db = AsyncMock()

    # Act
    result = await wallet_service.list_wallet_transactions(_USER_ID, 10, 0, db)

    # Assert — type is source-of-truth for the transaction kind, not the lifecycle state
    assert result.transactions[0].type == WalletTransactionType.CASHBACK_CREDIT


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "cashback_status",
    [
        "pending",  # awaiting confirmation
        "available",  # confirmed; in spendable balance
        "reversed",  # purchase reversed; cashback clawed back
    ],
)
async def test_list_wallet_transactions_passes_status_through(
    wallet_service: WalletService,
    cashback_client: Mock,
    cashback_status: str,
) -> None:
    # Arrange
    txn = _make_cashback_txn(status=cashback_status)
    cashback_client.list_by_user_id = AsyncMock(return_value=([txn], 1))
    db = AsyncMock()

    # Act
    result = await wallet_service.list_wallet_transactions(_USER_ID, 10, 0, db)

    # Assert — status is passed through unchanged so callers can read lifecycle state
    assert result.transactions[0].status == cashback_status
