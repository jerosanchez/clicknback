"""Unit tests for _run_verification_with_retry.

Covers the runner's retry lifecycle, outcome routing (confirm / force-reject /
hard-decline), stale-purchase guards, and in-flight cleanup guarantee.

The processor helpers (_confirm_purchase, _reject_purchase) are exercised
indirectly since they are called by the runner on each resolved outcome.

Module under test: app.purchases.jobs.verify_purchases._runner
"""

from datetime import datetime, timezone
from decimal import Decimal
from typing import cast
from unittest.mock import AsyncMock, MagicMock, create_autospec

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.audit.enums import AuditAction, AuditActorType, AuditOutcome
from app.core.audit.services import AuditTrailABC
from app.core.broker import MessageBrokerABC
from app.core.events.purchase_events import PurchaseConfirmed, PurchaseRejected
from app.purchases.jobs.verify_purchases import (
    PurchaseVerifierABC,
    SimulatedPurchaseVerifier,
    VerificationResult,
)
from app.purchases.jobs.verify_purchases._in_flight_tracker import (
    InMemoryInFlightTracker,
)
from app.purchases.jobs.verify_purchases._runner import (
    _run_verification_with_retry,  # pyright: ignore[reportPrivateUsage]
)
from app.purchases.models import Purchase
from app.purchases.repositories import PurchaseRepositoryABC
from app.purchases.schemas import PurchaseStatus

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_REJECTION_MERCHANT_ID = "f0000000-0000-0000-0000-000000000001"
_NORMAL_MERCHANT_ID = "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d"
_USER_ID = "b7e2c1a2-4f3a-4e2b-9c1a-8d2e3f4b5c6d"
_PURCHASE_ID = "aa000001-0000-0000-0000-000000000001"
_MAX_ATTEMPTS = 3
_FIXED_NOW = datetime(2026, 3, 11, 12, 0, 0, tzinfo=timezone.utc)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_purchase(
    *,
    purchase_id: str = _PURCHASE_ID,
    merchant_id: str = _NORMAL_MERCHANT_ID,
    status: str = "pending",
) -> Purchase:
    p = Purchase()
    p.id = purchase_id
    p.user_id = _USER_ID
    p.merchant_id = merchant_id
    p.amount = Decimal("100.00")
    p.currency = "EUR"
    p.status = status
    p.created_at = _FIXED_NOW.replace(tzinfo=None)
    return p


def _make_session_factory() -> tuple[async_sessionmaker[AsyncSession], AsyncMock]:
    session = AsyncMock()
    session.__aenter__ = AsyncMock(return_value=session)
    session.__aexit__ = AsyncMock(return_value=False)
    return (
        cast(async_sessionmaker[AsyncSession], MagicMock(return_value=session)),
        session,
    )


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def repository() -> MagicMock:
    return create_autospec(PurchaseRepositoryABC)


@pytest.fixture
def audit_trail() -> MagicMock:
    return create_autospec(AuditTrailABC)


@pytest.fixture
def message_broker() -> MagicMock:
    return create_autospec(MessageBrokerABC)


# ---------------------------------------------------------------------------
# Normal merchant — confirmed on first attempt
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_confirm_purchase_on_first_attempt(
    repository: MagicMock,
    audit_trail: MagicMock,
    message_broker: MagicMock,
) -> None:
    """A normal-merchant purchase is confirmed immediately on attempt 1."""
    # Arrange
    purchase = _make_purchase()
    session_factory, session = _make_session_factory()
    repository.get_by_id = AsyncMock(return_value=purchase)
    repository.update_status = AsyncMock()
    message_broker.publish = AsyncMock()
    audit_trail.record = AsyncMock()

    # Act
    await _run_verification_with_retry(
        purchase_id=_PURCHASE_ID,
        repository=repository,
        audit_trail=audit_trail,
        broker=message_broker,
        db_session_factory=session_factory,
        verifier=SimulatedPurchaseVerifier(
            rejection_merchant_id=_REJECTION_MERCHANT_ID
        ),
        max_attempts=_MAX_ATTEMPTS,
        retry_interval_seconds=0,
        datetime_provider=lambda: _FIXED_NOW,
        in_flight=InMemoryInFlightTracker(),
    )

    # Assert
    repository.update_status.assert_called_once_with(
        session, _PURCHASE_ID, PurchaseStatus.CONFIRMED.value
    )
    repository.get_by_id.assert_called_once()


@pytest.mark.asyncio
async def test_normal_purchase_publishes_confirmed_event(
    repository: MagicMock,
    audit_trail: MagicMock,
    message_broker: MagicMock,
) -> None:
    # Arrange
    purchase = _make_purchase()
    session_factory, _ = _make_session_factory()
    repository.get_by_id = AsyncMock(return_value=purchase)
    repository.update_status = AsyncMock()
    message_broker.publish = AsyncMock()
    audit_trail.record = AsyncMock()

    # Act
    await _run_verification_with_retry(
        purchase_id=_PURCHASE_ID,
        repository=repository,
        audit_trail=audit_trail,
        broker=message_broker,
        db_session_factory=session_factory,
        verifier=SimulatedPurchaseVerifier(
            rejection_merchant_id=_REJECTION_MERCHANT_ID
        ),
        max_attempts=_MAX_ATTEMPTS,
        retry_interval_seconds=0,
        datetime_provider=lambda: _FIXED_NOW,
        in_flight=InMemoryInFlightTracker(),
    )

    # Assert
    message_broker.publish.assert_called_once()
    event = message_broker.publish.call_args[0][0]
    assert isinstance(event, PurchaseConfirmed)
    assert event.purchase_id == _PURCHASE_ID
    assert event.verified_at == _FIXED_NOW


@pytest.mark.asyncio
async def test_normal_purchase_writes_confirmed_audit_record(
    repository: MagicMock,
    audit_trail: MagicMock,
    message_broker: MagicMock,
) -> None:
    # Arrange
    purchase = _make_purchase()
    session_factory, session = _make_session_factory()
    repository.get_by_id = AsyncMock(return_value=purchase)
    repository.update_status = AsyncMock()
    message_broker.publish = AsyncMock()
    audit_trail.record = AsyncMock()

    # Act
    await _run_verification_with_retry(
        purchase_id=_PURCHASE_ID,
        repository=repository,
        audit_trail=audit_trail,
        broker=message_broker,
        db_session_factory=session_factory,
        verifier=SimulatedPurchaseVerifier(
            rejection_merchant_id=_REJECTION_MERCHANT_ID
        ),
        max_attempts=_MAX_ATTEMPTS,
        retry_interval_seconds=0,
        datetime_provider=lambda: _FIXED_NOW,
        in_flight=InMemoryInFlightTracker(),
    )

    # Assert
    audit_trail.record.assert_called_once_with(
        db=session,
        actor_type=AuditActorType.system,
        actor_id=None,
        action=AuditAction.PURCHASE_CONFIRMED,
        resource_type="purchase",
        resource_id=_PURCHASE_ID,
        outcome=AuditOutcome.success,
        details={
            "merchant_id": purchase.merchant_id,
            "amount": str(purchase.amount),
            "currency": purchase.currency,
        },
    )


@pytest.mark.asyncio
async def test_in_flight_cleaned_up_after_confirmation(
    repository: MagicMock,
    audit_trail: MagicMock,
    message_broker: MagicMock,
) -> None:
    # Arrange
    purchase = _make_purchase()
    session_factory, _ = _make_session_factory()
    repository.get_by_id = AsyncMock(return_value=purchase)
    repository.update_status = AsyncMock()
    message_broker.publish = AsyncMock()
    audit_trail.record = AsyncMock()

    in_flight = InMemoryInFlightTracker()
    in_flight.add(_PURCHASE_ID, MagicMock())

    # Act
    await _run_verification_with_retry(
        purchase_id=_PURCHASE_ID,
        repository=repository,
        audit_trail=audit_trail,
        broker=message_broker,
        db_session_factory=session_factory,
        verifier=SimulatedPurchaseVerifier(
            rejection_merchant_id=_REJECTION_MERCHANT_ID
        ),
        max_attempts=_MAX_ATTEMPTS,
        retry_interval_seconds=0,
        datetime_provider=lambda: _FIXED_NOW,
        in_flight=in_flight,
    )

    # Assert
    assert not in_flight.contains(_PURCHASE_ID)


# ---------------------------------------------------------------------------
# Rejection merchant — force-rejected after max_attempts soft failures
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_rejection_merchant_force_rejected_after_max_attempts(
    repository: MagicMock,
    audit_trail: MagicMock,
    message_broker: MagicMock,
) -> None:
    """Soft failures on every attempt cause a force-reject after the retry loop."""
    # Arrange
    purchase = _make_purchase(merchant_id=_REJECTION_MERCHANT_ID)
    session_factory, session = _make_session_factory()
    repository.get_by_id = AsyncMock(return_value=purchase)
    repository.update_status = AsyncMock()
    message_broker.publish = AsyncMock()
    audit_trail.record = AsyncMock()

    # Act
    await _run_verification_with_retry(
        purchase_id=_PURCHASE_ID,
        repository=repository,
        audit_trail=audit_trail,
        broker=message_broker,
        db_session_factory=session_factory,
        verifier=SimulatedPurchaseVerifier(
            rejection_merchant_id=_REJECTION_MERCHANT_ID
        ),
        max_attempts=_MAX_ATTEMPTS,
        retry_interval_seconds=0,
        datetime_provider=lambda: _FIXED_NOW,
        in_flight=InMemoryInFlightTracker(),
    )

    # Assert
    # get_by_id: once per attempt in the retry loop + once for the force-reject fetch
    assert repository.get_by_id.call_count == _MAX_ATTEMPTS + 1
    repository.update_status.assert_called_once_with(
        session, _PURCHASE_ID, PurchaseStatus.REJECTED.value
    )


@pytest.mark.asyncio
async def test_rejection_merchant_publishes_rejected_event(
    repository: MagicMock,
    audit_trail: MagicMock,
    message_broker: MagicMock,
) -> None:
    # Arrange
    purchase = _make_purchase(merchant_id=_REJECTION_MERCHANT_ID)
    session_factory, _ = _make_session_factory()
    repository.get_by_id = AsyncMock(return_value=purchase)
    repository.update_status = AsyncMock()
    message_broker.publish = AsyncMock()
    audit_trail.record = AsyncMock()

    # Act
    await _run_verification_with_retry(
        purchase_id=_PURCHASE_ID,
        repository=repository,
        audit_trail=audit_trail,
        broker=message_broker,
        db_session_factory=session_factory,
        verifier=SimulatedPurchaseVerifier(
            rejection_merchant_id=_REJECTION_MERCHANT_ID
        ),
        max_attempts=_MAX_ATTEMPTS,
        retry_interval_seconds=0,
        datetime_provider=lambda: _FIXED_NOW,
        in_flight=InMemoryInFlightTracker(),
    )

    # Assert
    message_broker.publish.assert_called_once()
    event = message_broker.publish.call_args[0][0]
    assert isinstance(event, PurchaseRejected)
    assert event.purchase_id == _PURCHASE_ID
    assert event.failed_at == _FIXED_NOW
    assert "verification attempt" in event.reason


@pytest.mark.asyncio
async def test_rejection_merchant_writes_rejected_audit_record(
    repository: MagicMock,
    audit_trail: MagicMock,
    message_broker: MagicMock,
) -> None:
    # Arrange
    purchase = _make_purchase(merchant_id=_REJECTION_MERCHANT_ID)
    session_factory, _ = _make_session_factory()
    repository.get_by_id = AsyncMock(return_value=purchase)
    repository.update_status = AsyncMock()
    message_broker.publish = AsyncMock()
    audit_trail.record = AsyncMock()

    # Act
    await _run_verification_with_retry(
        purchase_id=_PURCHASE_ID,
        repository=repository,
        audit_trail=audit_trail,
        broker=message_broker,
        db_session_factory=session_factory,
        verifier=SimulatedPurchaseVerifier(
            rejection_merchant_id=_REJECTION_MERCHANT_ID
        ),
        max_attempts=_MAX_ATTEMPTS,
        retry_interval_seconds=0,
        datetime_provider=lambda: _FIXED_NOW,
        in_flight=InMemoryInFlightTracker(),
    )

    # Assert
    audit_trail.record.assert_called_once()
    kwargs = audit_trail.record.call_args.kwargs
    assert kwargs["action"] == AuditAction.PURCHASE_REJECTED
    assert kwargs["actor_type"] == AuditActorType.system
    assert kwargs["actor_id"] is None
    assert kwargs["resource_id"] == _PURCHASE_ID
    assert kwargs["outcome"] == AuditOutcome.success
    assert kwargs["details"]["attempt"] == _MAX_ATTEMPTS


@pytest.mark.asyncio
async def test_rejection_merchant_cleans_up_in_flight(
    repository: MagicMock,
    audit_trail: MagicMock,
    message_broker: MagicMock,
) -> None:
    # Arrange
    purchase = _make_purchase(merchant_id=_REJECTION_MERCHANT_ID)
    session_factory, _ = _make_session_factory()
    repository.get_by_id = AsyncMock(return_value=purchase)
    repository.update_status = AsyncMock()
    message_broker.publish = AsyncMock()
    audit_trail.record = AsyncMock()

    in_flight = InMemoryInFlightTracker()
    in_flight.add(_PURCHASE_ID, MagicMock())

    # Act
    await _run_verification_with_retry(
        purchase_id=_PURCHASE_ID,
        repository=repository,
        audit_trail=audit_trail,
        broker=message_broker,
        db_session_factory=session_factory,
        verifier=SimulatedPurchaseVerifier(
            rejection_merchant_id=_REJECTION_MERCHANT_ID
        ),
        max_attempts=_MAX_ATTEMPTS,
        retry_interval_seconds=0,
        datetime_provider=lambda: _FIXED_NOW,
        in_flight=in_flight,
    )

    # Assert
    assert not in_flight.contains(_PURCHASE_ID)


@pytest.mark.asyncio
async def test_purchase_id_in_flight_during_retries(
    repository: MagicMock,
    audit_trail: MagicMock,
    message_broker: MagicMock,
) -> None:
    """Ensures purchase_id stays in flight during retries and is not available for other workers."""
    # Arrange
    purchase = _make_purchase()
    session_factory, _ = _make_session_factory()
    repository.get_by_id = AsyncMock(return_value=purchase)
    repository.update_status = AsyncMock()
    message_broker.publish = AsyncMock()
    audit_trail.record = AsyncMock()

    in_flight = InMemoryInFlightTracker()

    class AlwaysFailVerifier(PurchaseVerifierABC):
        async def verify(self, purchase: Purchase, attempt: int) -> VerificationResult:
            return VerificationResult(disposition="pending")

    # Act
    await _run_verification_with_retry(
        purchase_id=_PURCHASE_ID,
        repository=repository,
        audit_trail=audit_trail,
        broker=message_broker,
        db_session_factory=session_factory,
        verifier=AlwaysFailVerifier(),
        max_attempts=_MAX_ATTEMPTS,
        retry_interval_seconds=0,
        datetime_provider=lambda: _FIXED_NOW,
        in_flight=in_flight,
    )

    # Assert
    assert not in_flight.contains(_PURCHASE_ID)


# ---------------------------------------------------------------------------
# Hard decline — immediate rejection from verifier
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_hard_decline_rejects_immediately_without_retrying(
    repository: MagicMock,
    audit_trail: MagicMock,
    message_broker: MagicMock,
) -> None:
    """A verifier-returned ``"rejected"`` disposition stops the loop immediately."""
    # Arrange
    purchase = _make_purchase()
    session_factory, session = _make_session_factory()
    repository.get_by_id = AsyncMock(return_value=purchase)
    repository.update_status = AsyncMock()
    message_broker.publish = AsyncMock()
    audit_trail.record = AsyncMock()

    hard_decline_verifier = MagicMock()
    hard_decline_verifier.verify = AsyncMock(
        return_value=VerificationResult(
            disposition="rejected", reason="Insufficient funds."
        )
    )

    # Act
    await _run_verification_with_retry(
        purchase_id=_PURCHASE_ID,
        repository=repository,
        audit_trail=audit_trail,
        broker=message_broker,
        db_session_factory=session_factory,
        verifier=hard_decline_verifier,
        max_attempts=_MAX_ATTEMPTS,
        retry_interval_seconds=0,
        datetime_provider=lambda: _FIXED_NOW,
        in_flight=InMemoryInFlightTracker(),
    )

    # Assert
    hard_decline_verifier.verify.assert_called_once()
    repository.update_status.assert_called_once_with(
        session, _PURCHASE_ID, PurchaseStatus.REJECTED.value
    )
    event = message_broker.publish.call_args[0][0]
    assert isinstance(event, PurchaseRejected)
    assert event.reason == "Insufficient funds."


# ---------------------------------------------------------------------------
# Stale purchase — no operation when not pending
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_no_action_when_purchase_already_confirmed(
    repository: MagicMock,
    audit_trail: MagicMock,
    message_broker: MagicMock,
) -> None:
    """If the purchase is already confirmed, the loop exits silently."""
    # Arrange
    purchase = _make_purchase(status=PurchaseStatus.CONFIRMED.value)
    session_factory, _ = _make_session_factory()
    repository.get_by_id = AsyncMock(return_value=purchase)
    repository.update_status = AsyncMock()
    message_broker.publish = AsyncMock()
    audit_trail.record = AsyncMock()

    # Act
    await _run_verification_with_retry(
        purchase_id=_PURCHASE_ID,
        repository=repository,
        audit_trail=audit_trail,
        broker=message_broker,
        db_session_factory=session_factory,
        verifier=SimulatedPurchaseVerifier(
            rejection_merchant_id=_REJECTION_MERCHANT_ID
        ),
        max_attempts=_MAX_ATTEMPTS,
        retry_interval_seconds=0,
        datetime_provider=lambda: _FIXED_NOW,
        in_flight=InMemoryInFlightTracker(),
    )

    # Assert
    repository.update_status.assert_not_called()
    message_broker.publish.assert_not_called()
    audit_trail.record.assert_not_called()


@pytest.mark.asyncio
async def test_no_action_when_purchase_not_found(
    repository: MagicMock,
    audit_trail: MagicMock,
    message_broker: MagicMock,
) -> None:
    """If get_by_id returns None, the loop exits silently."""
    # Arrange
    session_factory, _ = _make_session_factory()
    repository.get_by_id = AsyncMock(return_value=None)
    repository.update_status = AsyncMock()
    message_broker.publish = AsyncMock()
    audit_trail.record = AsyncMock()

    # A
    await _run_verification_with_retry(
        purchase_id=_PURCHASE_ID,
        repository=repository,
        audit_trail=audit_trail,
        broker=message_broker,
        db_session_factory=session_factory,
        verifier=SimulatedPurchaseVerifier(
            rejection_merchant_id=_REJECTION_MERCHANT_ID
        ),
        max_attempts=_MAX_ATTEMPTS,
        retry_interval_seconds=0,
        datetime_provider=lambda: _FIXED_NOW,
        in_flight=InMemoryInFlightTracker(),
    )

    # Assert
    repository.update_status.assert_not_called()
    message_broker.publish.assert_not_called()
