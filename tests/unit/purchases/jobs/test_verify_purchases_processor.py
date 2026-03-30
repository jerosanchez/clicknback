"""Unit tests for verify_purchases processor (_confirm_purchase, _reject_purchase).

Covers collaborator verification: ensures the processor correctly delegates to
the helper function, updates status, reverses balances, commits the transaction,
and publishes domain events with correct financial details.

Module under test: app.purchases.jobs.verify_purchases._processor
"""

from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, Mock, create_autospec

import pytest

from app.core.broker import MessageBrokerABC
from app.core.events.purchase_events import PurchaseConfirmed, PurchaseRejected
from app.purchases.clients import CashbackClientABC, WalletsClientABC
from app.purchases.jobs.verify_purchases._processor import (
    _confirm_purchase,  # pyright: ignore[reportPrivateUsage]
    _reject_purchase,  # pyright: ignore[reportPrivateUsage]
)
from app.purchases.models import Purchase
from app.purchases.repositories import PurchaseRepositoryABC
from app.purchases.schemas import PurchaseStatus

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_PURCHASE_ID = "p1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d"
_USER_ID = "u1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d"
_MERCHANT_ID = "m1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d"
_VERIFIED_AT = datetime(2026, 3, 11, 12, 0, 0, tzinfo=timezone.utc)
_FAILED_AT = datetime(2026, 3, 11, 13, 0, 0, tzinfo=timezone.utc)
_AMOUNT = Decimal("100.00")
_CASHBACK_AMOUNT = Decimal("10.00")
_CURRENCY = "EUR"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def purchase() -> Purchase:
    return Purchase(
        id=_PURCHASE_ID,
        user_id=_USER_ID,
        merchant_id=_MERCHANT_ID,
        offer_id="o1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d",
        external_id="ext-123",
        amount=_AMOUNT,
        cashback_amount=_CASHBACK_AMOUNT,
        currency=_CURRENCY,
        status=PurchaseStatus.PENDING.value,
    )


@pytest.fixture
def db() -> Mock:
    mock = Mock()
    mock.commit = AsyncMock()
    return mock


@pytest.fixture
def repository() -> Mock:
    return create_autospec(PurchaseRepositoryABC)


@pytest.fixture
def wallets_client() -> Mock:
    return create_autospec(WalletsClientABC)


@pytest.fixture
def cashback_client() -> Mock:
    return create_autospec(CashbackClientABC)


@pytest.fixture
def broker() -> Mock:
    return create_autospec(MessageBrokerABC)


# ---------------------------------------------------------------------------
# _confirm_purchase tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_confirm_purchase_calls_apply_helper(
    purchase: Purchase,
    db: Mock,
    repository: Mock,
    wallets_client: Mock,
    cashback_client: Mock,
    broker: Mock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify _confirm_purchase calls apply_purchase_confirmation with correct args."""
    # Arrange
    apply_helper_mock = AsyncMock()
    monkeypatch.setattr(
        "app.purchases.jobs.verify_purchases._processor.apply_purchase_confirmation",
        apply_helper_mock,
    )

    # Act
    await _confirm_purchase(
        purchase=purchase,
        verified_at=_VERIFIED_AT,
        db=db,
        repository=repository,
        wallets_client=wallets_client,
        cashback_client=cashback_client,
        broker=broker,
    )

    # Assert
    apply_helper_mock.assert_called_once_with(
        purchase=purchase,
        db=db,
        repository=repository,
        cashback_client=cashback_client,
        wallets_client=wallets_client,
    )


@pytest.mark.asyncio
async def test_confirm_purchase_commits_after_helper(
    purchase: Purchase,
    db: Mock,
    repository: Mock,
    wallets_client: Mock,
    cashback_client: Mock,
    broker: Mock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify _confirm_purchase commits after calling the helper."""
    # Arrange
    apply_helper_mock = AsyncMock()
    monkeypatch.setattr(
        "app.purchases.jobs.verify_purchases._processor.apply_purchase_confirmation",
        apply_helper_mock,
    )

    # Act
    await _confirm_purchase(
        purchase=purchase,
        verified_at=_VERIFIED_AT,
        db=db,
        repository=repository,
        wallets_client=wallets_client,
        cashback_client=cashback_client,
        broker=broker,
    )

    # Assert
    db.commit.assert_called_once()


@pytest.mark.asyncio
async def test_confirm_purchase_publishes_confirmed_event(
    purchase: Purchase,
    db: Mock,
    repository: Mock,
    wallets_client: Mock,
    cashback_client: Mock,
    broker: Mock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify _confirm_purchase publishes PurchaseConfirmed event."""
    # Arrange
    apply_helper_mock = AsyncMock()
    monkeypatch.setattr(
        "app.purchases.jobs.verify_purchases._processor.apply_purchase_confirmation",
        apply_helper_mock,
    )
    broker.publish = AsyncMock()

    # Act
    await _confirm_purchase(
        purchase=purchase,
        verified_at=_VERIFIED_AT,
        db=db,
        repository=repository,
        wallets_client=wallets_client,
        cashback_client=cashback_client,
        broker=broker,
    )

    # Assert
    broker.publish.assert_called_once()
    event = broker.publish.call_args[0][0]
    assert isinstance(event, PurchaseConfirmed)


@pytest.mark.asyncio
async def test_confirm_purchase_event_contains_financial_details(
    purchase: Purchase,
    db: Mock,
    repository: Mock,
    wallets_client: Mock,
    cashback_client: Mock,
    broker: Mock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify event contains all purchase financial details."""
    # Arrange
    apply_helper_mock = AsyncMock()
    monkeypatch.setattr(
        "app.purchases.jobs.verify_purchases._processor.apply_purchase_confirmation",
        apply_helper_mock,
    )
    broker.publish = AsyncMock()

    # Act
    await _confirm_purchase(
        purchase=purchase,
        verified_at=_VERIFIED_AT,
        db=db,
        repository=repository,
        wallets_client=wallets_client,
        cashback_client=cashback_client,
        broker=broker,
    )

    # Assert
    event: PurchaseConfirmed = broker.publish.call_args[0][0]
    assert event.purchase_id == _PURCHASE_ID
    assert event.user_id == _USER_ID
    assert event.merchant_id == _MERCHANT_ID
    assert event.amount == _AMOUNT
    assert event.currency == _CURRENCY
    assert event.cashback_amount == _CASHBACK_AMOUNT
    assert event.verified_at == _VERIFIED_AT


# ---------------------------------------------------------------------------
# _reject_purchase tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_reject_purchase_updates_status_to_rejected(
    purchase: Purchase,
    db: Mock,
    repository: Mock,
    wallets_client: Mock,
    cashback_client: Mock,
    broker: Mock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify _reject_purchase updates purchase status to REJECTED."""
    # Arrange
    apply_helper_mock = AsyncMock()
    monkeypatch.setattr(
        "app.purchases.jobs.verify_purchases._processor.apply_purchase_confirmation",
        apply_helper_mock,
    )
    repository.update_status = AsyncMock()

    # Act
    await _reject_purchase(
        purchase=purchase,
        reason="Bank declined",
        attempt=1,
        failed_at=_FAILED_AT,
        db=db,
        repository=repository,
        wallets_client=wallets_client,
        cashback_client=cashback_client,
        broker=broker,
    )

    # Assert
    repository.update_status.assert_called_once_with(
        db, _PURCHASE_ID, PurchaseStatus.REJECTED.value
    )


@pytest.mark.asyncio
async def test_reject_purchase_reverses_cashback_when_nonzero(
    purchase: Purchase,
    db: Mock,
    repository: Mock,
    wallets_client: Mock,
    cashback_client: Mock,
    broker: Mock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify _reject_purchase reverses cashback transaction when amount > 0."""
    # Arrange
    apply_helper_mock = AsyncMock()
    monkeypatch.setattr(
        "app.purchases.jobs.verify_purchases._processor.apply_purchase_confirmation",
        apply_helper_mock,
    )
    repository.update_status = AsyncMock()
    cashback_client.reverse = AsyncMock()

    # Act
    await _reject_purchase(
        purchase=purchase,
        reason="Bank declined",
        attempt=1,
        failed_at=_FAILED_AT,
        db=db,
        repository=repository,
        wallets_client=wallets_client,
        cashback_client=cashback_client,
        broker=broker,
    )

    # Assert
    cashback_client.reverse.assert_called_once_with(db, _PURCHASE_ID)


@pytest.mark.asyncio
async def test_reject_purchase_reverses_wallet_pending_when_nonzero(
    purchase: Purchase,
    db: Mock,
    repository: Mock,
    wallets_client: Mock,
    cashback_client: Mock,
    broker: Mock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify _reject_purchase reverses pending wallet balance when cashback > 0."""
    # Arrange
    apply_helper_mock = AsyncMock()
    monkeypatch.setattr(
        "app.purchases.jobs.verify_purchases._processor.apply_purchase_confirmation",
        apply_helper_mock,
    )
    repository.update_status = AsyncMock()
    cashback_client.reverse = AsyncMock()
    wallets_client.reverse_pending = AsyncMock()

    # Act
    await _reject_purchase(
        purchase=purchase,
        reason="Bank declined",
        attempt=1,
        failed_at=_FAILED_AT,
        db=db,
        repository=repository,
        wallets_client=wallets_client,
        cashback_client=cashback_client,
        broker=broker,
    )

    # Assert
    wallets_client.reverse_pending.assert_called_once_with(
        db, _USER_ID, _CASHBACK_AMOUNT
    )


@pytest.mark.asyncio
async def test_reject_purchase_skips_reversal_when_cashback_zero(
    purchase: Purchase,
    db: Mock,
    repository: Mock,
    wallets_client: Mock,
    cashback_client: Mock,
    broker: Mock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify _reject_purchase skips reversal when cashback is zero."""
    # Arrange
    zero_cashback_purchase = Purchase(
        id=_PURCHASE_ID,
        user_id=_USER_ID,
        merchant_id=_MERCHANT_ID,
        offer_id="o1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d",
        external_id="ext-123",
        amount=_AMOUNT,
        cashback_amount=Decimal("0"),
        currency=_CURRENCY,
        status=PurchaseStatus.PENDING.value,
    )
    apply_helper_mock = AsyncMock()
    monkeypatch.setattr(
        "app.purchases.jobs.verify_purchases._processor.apply_purchase_confirmation",
        apply_helper_mock,
    )
    repository.update_status = AsyncMock()
    cashback_client.reverse = AsyncMock()
    wallets_client.reverse_pending = AsyncMock()

    # Act
    await _reject_purchase(
        purchase=zero_cashback_purchase,
        reason="Bank declined",
        attempt=1,
        failed_at=_FAILED_AT,
        db=db,
        repository=repository,
        wallets_client=wallets_client,
        cashback_client=cashback_client,
        broker=broker,
    )

    # Assert
    cashback_client.reverse.assert_not_called()
    wallets_client.reverse_pending.assert_not_called()


@pytest.mark.asyncio
async def test_reject_purchase_commits_after_reversal(
    purchase: Purchase,
    db: Mock,
    repository: Mock,
    wallets_client: Mock,
    cashback_client: Mock,
    broker: Mock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify _reject_purchase commits after reversing balance."""
    # Arrange
    apply_helper_mock = AsyncMock()
    monkeypatch.setattr(
        "app.purchases.jobs.verify_purchases._processor.apply_purchase_confirmation",
        apply_helper_mock,
    )
    repository.update_status = AsyncMock()
    cashback_client.reverse = AsyncMock()
    wallets_client.reverse_pending = AsyncMock()

    # Act
    await _reject_purchase(
        purchase=purchase,
        reason="Bank declined",
        attempt=1,
        failed_at=_FAILED_AT,
        db=db,
        repository=repository,
        wallets_client=wallets_client,
        cashback_client=cashback_client,
        broker=broker,
    )

    # Assert
    db.commit.assert_called_once()


@pytest.mark.asyncio
async def test_reject_purchase_publishes_rejected_event(
    purchase: Purchase,
    db: Mock,
    repository: Mock,
    wallets_client: Mock,
    cashback_client: Mock,
    broker: Mock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify _reject_purchase publishes PurchaseRejected event."""
    # Arrange
    apply_helper_mock = AsyncMock()
    monkeypatch.setattr(
        "app.purchases.jobs.verify_purchases._processor.apply_purchase_confirmation",
        apply_helper_mock,
    )
    repository.update_status = AsyncMock()
    cashback_client.reverse = AsyncMock()
    wallets_client.reverse_pending = AsyncMock()
    broker.publish = AsyncMock()

    # Act
    await _reject_purchase(
        purchase=purchase,
        reason="Bank declined",
        attempt=1,
        failed_at=_FAILED_AT,
        db=db,
        repository=repository,
        wallets_client=wallets_client,
        cashback_client=cashback_client,
        broker=broker,
    )

    # Assert
    broker.publish.assert_called_once()
    event = broker.publish.call_args[0][0]
    assert isinstance(event, PurchaseRejected)


@pytest.mark.asyncio
async def test_reject_purchase_event_contains_details(
    purchase: Purchase,
    db: Mock,
    repository: Mock,
    wallets_client: Mock,
    cashback_client: Mock,
    broker: Mock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify rejection event contains all required details."""
    # Arrange
    apply_helper_mock = AsyncMock()
    monkeypatch.setattr(
        "app.purchases.jobs.verify_purchases._processor.apply_purchase_confirmation",
        apply_helper_mock,
    )
    repository.update_status = AsyncMock()
    cashback_client.reverse = AsyncMock()
    wallets_client.reverse_pending = AsyncMock()
    broker.publish = AsyncMock()
    reason = "Bank declined — insufficient funds"

    # Act
    await _reject_purchase(
        purchase=purchase,
        reason=reason,
        attempt=2,
        failed_at=_FAILED_AT,
        db=db,
        repository=repository,
        wallets_client=wallets_client,
        cashback_client=cashback_client,
        broker=broker,
    )

    # Assert
    event: PurchaseRejected = broker.publish.call_args[0][0]
    assert event.purchase_id == _PURCHASE_ID
    assert event.user_id == _USER_ID
    assert event.merchant_id == _MERCHANT_ID
    assert event.amount == _AMOUNT
    assert event.currency == _CURRENCY
    assert event.reason == reason
    assert event.failed_at == _FAILED_AT
