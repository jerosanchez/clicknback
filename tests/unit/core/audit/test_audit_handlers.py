"""Tests for audit event handlers.

Each handler maps one domain event type to an audit log record.
These tests verify the mapping (actor, action, resource, details) and the
shared persistence behavior (_persist_audit_log).
"""

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from unittest.mock import AsyncMock

import pytest

from app.core.audit.enums import AuditAction, AuditActorType, AuditOutcome

# Testing internal handlers to verify handler behavior and event-to-audit mapping.
# See docs/guidelines/unit-testing.md § Testing Private Implementation Details.
from app.core.audit.handlers import (
    _handle_purchase_confirmed,  # pyright: ignore[reportPrivateUsage]
    _handle_purchase_rejected,  # pyright: ignore[reportPrivateUsage]
    _handle_purchase_reversed,  # pyright: ignore[reportPrivateUsage]
)
from app.core.audit.models import AuditLog
from app.core.audit.repositories import AuditTrailRepositoryABC
from app.core.events.purchase_events import (
    PurchaseConfirmed,
    PurchaseRejected,
    PurchaseReversed,
)

_FIXED_NOW = datetime(2025, 3, 26, 12, 0, 0, tzinfo=timezone.utc)
_PURCHASE_ID = "purchase-111"
_USER_ID = "user-222"
_ADMIN_ID = "admin-333"
_MERCHANT_ID = "merchant-444"


# ---------------------------------------------------------------------------
# PurchaseConfirmed → PURCHASE_CONFIRMED audit record
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_handle_purchase_confirmed_persists_correct_audit_record() -> None:
    """PurchaseConfirmed maps to a system-actor PURCHASE_CONFIRMED audit log."""
    # Arrange
    db = AsyncMock()
    repository = AsyncMock(spec=AuditTrailRepositoryABC)
    event = PurchaseConfirmed(
        purchase_id=_PURCHASE_ID,
        user_id=_USER_ID,
        merchant_id=_MERCHANT_ID,
        amount=Decimal("100.00"),
        currency="EUR",
        cashback_amount=Decimal("5.00"),
        verified_at=_FIXED_NOW,
    )

    # Act
    await _handle_purchase_confirmed(
        db=db,
        repository=repository,
        datetime_provider=lambda: _FIXED_NOW,
        event=event,
    )

    # Assert
    repository.add.assert_called_once()
    audit_log: AuditLog = repository.add.call_args[0][1]
    assert audit_log.actor_type == AuditActorType.system.value
    assert audit_log.actor_id is None
    assert audit_log.action == AuditAction.PURCHASE_CONFIRMED.value
    assert audit_log.resource_type == "purchase"
    assert audit_log.resource_id == _PURCHASE_ID
    assert audit_log.outcome == AuditOutcome.success.value
    assert audit_log.details is not None
    assert audit_log.details["merchant_id"] == _MERCHANT_ID
    assert audit_log.details["amount"] == "100.00"
    assert audit_log.details["currency"] == "EUR"
    assert audit_log.details["cashback_amount"] == "5.00"


# ---------------------------------------------------------------------------
# PurchaseRejected → PURCHASE_REJECTED audit record
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_handle_purchase_rejected_persists_correct_audit_record() -> None:
    """PurchaseRejected maps to a system-actor PURCHASE_REJECTED audit log."""
    # Arrange
    db = AsyncMock()
    repository = AsyncMock(spec=AuditTrailRepositoryABC)
    event = PurchaseRejected(
        purchase_id=_PURCHASE_ID,
        user_id=_USER_ID,
        merchant_id=_MERCHANT_ID,
        amount=Decimal("50.00"),
        currency="EUR",
        failed_at=_FIXED_NOW,
        reason="Bank declined",
    )

    # Act
    await _handle_purchase_rejected(
        db=db,
        repository=repository,
        datetime_provider=lambda: _FIXED_NOW,
        event=event,
    )

    # Assert
    repository.add.assert_called_once()
    audit_log: AuditLog = repository.add.call_args[0][1]
    assert audit_log.actor_type == AuditActorType.system.value
    assert audit_log.actor_id is None
    assert audit_log.action == AuditAction.PURCHASE_REJECTED.value
    assert audit_log.resource_type == "purchase"
    assert audit_log.resource_id == _PURCHASE_ID
    assert audit_log.outcome == AuditOutcome.success.value
    assert audit_log.details is not None
    assert audit_log.details["merchant_id"] == _MERCHANT_ID
    assert audit_log.details["amount"] == "50.00"
    assert audit_log.details["currency"] == "EUR"
    assert audit_log.details["reason"] == "Bank declined"


# ---------------------------------------------------------------------------
# PurchaseReversed → PURCHASE_REVERSED audit record
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_handle_purchase_reversed_persists_correct_audit_record() -> None:
    """PurchaseReversed maps to an admin-actor PURCHASE_REVERSED audit log."""
    # Arrange
    db = AsyncMock()
    repository = AsyncMock(spec=AuditTrailRepositoryABC)
    event = PurchaseReversed(
        purchase_id=_PURCHASE_ID,
        user_id=_USER_ID,
        admin_id=_ADMIN_ID,
        merchant_id=_MERCHANT_ID,
        amount=Decimal("75.00"),
        currency="EUR",
        prior_status="confirmed",
    )

    # Act
    await _handle_purchase_reversed(
        db=db,
        repository=repository,
        datetime_provider=lambda: _FIXED_NOW,
        event=event,
    )

    # Assert
    repository.add.assert_called_once()
    audit_log: AuditLog = repository.add.call_args[0][1]
    assert audit_log.actor_type == AuditActorType.admin.value
    assert audit_log.actor_id == _ADMIN_ID
    assert audit_log.action == AuditAction.PURCHASE_REVERSED.value
    assert audit_log.resource_type == "purchase"
    assert audit_log.resource_id == _PURCHASE_ID
    assert audit_log.outcome == AuditOutcome.success.value
    assert audit_log.details is not None
    assert audit_log.details == {"prior_status": "confirmed"}


# ---------------------------------------------------------------------------
# Shared persistence behaviour (_persist_audit_log via any handler)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_audit_log_datetime_is_converted_to_naive_utc() -> None:
    """occurred_at is always stored as naive UTC regardless of input timezone."""
    # Arrange
    db = AsyncMock()
    repository = AsyncMock(spec=AuditTrailRepositoryABC)
    utc_plus_2 = datetime(2025, 3, 26, 14, 0, 0, tzinfo=timezone(timedelta(hours=2)))
    event = PurchaseConfirmed(
        purchase_id=_PURCHASE_ID,
        user_id=_USER_ID,
        merchant_id=_MERCHANT_ID,
        amount=Decimal("10.00"),
        currency="EUR",
        cashback_amount=Decimal("1.00"),
        verified_at=utc_plus_2,
    )

    # Act
    await _handle_purchase_confirmed(
        db=db,
        repository=repository,
        datetime_provider=lambda: utc_plus_2,
        event=event,
    )

    # Assert
    audit_log: AuditLog = repository.add.call_args[0][1]
    assert audit_log.occurred_at == datetime(2025, 3, 26, 12, 0, 0)
    assert audit_log.occurred_at.tzinfo is None
