from decimal import Decimal
from unittest.mock import AsyncMock, create_autospec

import pytest

from app.wallets.models import Wallet
from app.wallets.repositories import WalletRepositoryABC
from app.wallets.schemas import WalletSummaryOut
from app.wallets.services import WalletService

# ──────────────────────────────────────────────────────────────────────────────
# Fixtures
# ──────────────────────────────────────────────────────────────────────────────

_USER_ID = "b7e2c1a2-4f3a-4e2b-9c1a-8d2e3f4b5c6d"


@pytest.fixture
def wallet_repository() -> AsyncMock:
    return create_autospec(WalletRepositoryABC)


@pytest.fixture
def wallet_service(wallet_repository: AsyncMock) -> WalletService:
    return WalletService(repository=wallet_repository)


def _make_wallet(**overrides: object) -> Wallet:
    wallet = Wallet()
    wallet.user_id = _USER_ID
    wallet.pending_balance = Decimal("5.00")
    wallet.available_balance = Decimal("25.50")
    wallet.paid_balance = Decimal("100.00")
    for key, value in overrides.items():
        setattr(wallet, key, value)
    return wallet


# ──────────────────────────────────────────────────────────────────────────────
# WalletService.get_wallet_summary — happy path
# ──────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_wallet_summary_returns_balances_on_existing_wallet(
    wallet_service: WalletService,
    wallet_repository: AsyncMock,
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
    wallet_repository: AsyncMock,
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
