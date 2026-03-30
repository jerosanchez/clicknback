"""Unit tests for apply_purchase_confirmation.

Tests the core purchase confirmation state transition in isolation:

- Status update to CONFIRMED.
- Cashback transaction confirmation.
- Wallet balance move from pending to available.
- Zero-cashback guard (no cashback or wallet calls when amount is 0).
- Return value is the confirmed purchase.

Module under test: app.purchases._purchase_confirmation
"""

from decimal import Decimal
from unittest.mock import AsyncMock, Mock, create_autospec

import pytest

from app.purchases._helpers import apply_purchase_confirmation
from app.purchases.clients import CashbackClientABC, WalletsClientABC
from app.purchases.models import Purchase
from app.purchases.repositories import PurchaseRepositoryABC
from app.purchases.schemas import PurchaseStatus

# ──────────────────────────────────────────────────────────────────────────────
# Constants
# ──────────────────────────────────────────────────────────────────────────────

_PURCHASE_ID = "bb000001-0000-0000-0000-000000000001"
_USER_ID = "c7e2c1a2-4f3a-4e2b-9c1a-8d2e3f4b5c7d"
_CASHBACK_AMOUNT = Decimal("10.00")

# ──────────────────────────────────────────────────────────────────────────────
# Fixtures
# ──────────────────────────────────────────────────────────────────────────────


@pytest.fixture
def repository() -> Mock:
    return create_autospec(PurchaseRepositoryABC)


@pytest.fixture
def cashback_client() -> Mock:
    return create_autospec(CashbackClientABC)


@pytest.fixture
def wallets_client() -> Mock:
    return create_autospec(WalletsClientABC)


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────


def _make_purchase(
    *,
    purchase_id: str = _PURCHASE_ID,
    user_id: str = _USER_ID,
    cashback_amount: Decimal = _CASHBACK_AMOUNT,
    status: str = "pending",
) -> Purchase:
    p = Purchase()
    p.id = purchase_id
    p.user_id = user_id
    p.cashback_amount = cashback_amount
    p.status = status
    return p


# ──────────────────────────────────────────────────────────────────────────────
# apply_purchase_confirmation — state transition
# ──────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_apply_purchase_confirmation_updates_status_to_confirmed(
    repository: Mock,
    cashback_client: Mock,
    wallets_client: Mock,
) -> None:
    # Arrange
    db = AsyncMock()
    purchase = _make_purchase()
    repository.update_status.return_value = _make_purchase(status="confirmed")

    # Act
    await apply_purchase_confirmation(
        purchase=purchase,
        db=db,
        repository=repository,
        cashback_client=cashback_client,
        wallets_client=wallets_client,
    )

    # Assert
    repository.update_status.assert_called_once_with(
        db, _PURCHASE_ID, PurchaseStatus.CONFIRMED.value
    )


@pytest.mark.asyncio
async def test_apply_purchase_confirmation_returns_confirmed_purchase(
    repository: Mock,
    cashback_client: Mock,
    wallets_client: Mock,
) -> None:
    # Arrange
    db = AsyncMock()
    purchase = _make_purchase()
    confirmed = _make_purchase(status="confirmed")
    repository.update_status.return_value = confirmed

    # Act
    result = await apply_purchase_confirmation(
        purchase=purchase,
        db=db,
        repository=repository,
        cashback_client=cashback_client,
        wallets_client=wallets_client,
    )

    # Assert
    assert result.status == "confirmed"
    assert result is confirmed


@pytest.mark.asyncio
async def test_apply_purchase_confirmation_confirms_cashback_transaction(
    repository: Mock,
    cashback_client: Mock,
    wallets_client: Mock,
) -> None:
    # Arrange
    db = AsyncMock()
    purchase = _make_purchase(cashback_amount=_CASHBACK_AMOUNT)
    repository.update_status.return_value = _make_purchase(status="confirmed")

    # Act
    await apply_purchase_confirmation(
        purchase=purchase,
        db=db,
        repository=repository,
        cashback_client=cashback_client,
        wallets_client=wallets_client,
    )

    # Assert
    cashback_client.confirm.assert_called_once_with(db, _PURCHASE_ID)


@pytest.mark.asyncio
async def test_apply_purchase_confirmation_moves_pending_balance_to_available(
    repository: Mock,
    cashback_client: Mock,
    wallets_client: Mock,
) -> None:
    # Arrange
    db = AsyncMock()
    purchase = _make_purchase(cashback_amount=_CASHBACK_AMOUNT)
    repository.update_status.return_value = _make_purchase(status="confirmed")

    # Act
    await apply_purchase_confirmation(
        purchase=purchase,
        db=db,
        repository=repository,
        cashback_client=cashback_client,
        wallets_client=wallets_client,
    )

    # Assert
    wallets_client.confirm_pending.assert_called_once_with(
        db, _USER_ID, _CASHBACK_AMOUNT
    )


@pytest.mark.asyncio
async def test_apply_purchase_confirmation_skips_cashback_and_wallet_when_amount_is_zero(
    repository: Mock,
    cashback_client: Mock,
    wallets_client: Mock,
) -> None:
    # Arrange
    db = AsyncMock()
    purchase = _make_purchase(cashback_amount=Decimal("0"))
    repository.update_status.return_value = _make_purchase(
        cashback_amount=Decimal("0"), status="confirmed"
    )

    # Act
    await apply_purchase_confirmation(
        purchase=purchase,
        db=db,
        repository=repository,
        cashback_client=cashback_client,
        wallets_client=wallets_client,
    )

    # Assert
    cashback_client.confirm.assert_not_called()
    wallets_client.confirm_pending.assert_not_called()
