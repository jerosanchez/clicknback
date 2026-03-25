from datetime import datetime, timezone
from decimal import Decimal
from typing import cast
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.purchases.jobs.verify_purchases._dispatcher import (
    _dispatch_pending_purchases,  # pyright: ignore[reportPrivateUsage]
)
from app.purchases.jobs.verify_purchases._in_flight_tracker import (
    InMemoryInFlightTracker,
)
from app.purchases.models import Purchase
from app.purchases.repositories import PurchaseRepositoryABC

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_NORMAL_MERCHANT_ID = "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d"
_USER_ID = "b7e2c1a2-4f3a-4e2b-9c1a-8d2e3f4b5c6d"
_FIXED_NOW = datetime(2026, 3, 11, 12, 0, 0, tzinfo=timezone.utc)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_purchase(
    *, purchase_id: str = "aa000001-0000-0000-0000-000000000001"
) -> Purchase:
    p = Purchase()
    p.id = purchase_id
    p.user_id = _USER_ID
    p.merchant_id = _NORMAL_MERCHANT_ID
    p.amount = Decimal("100.00")
    p.currency = "EUR"
    p.status = "pending"
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
    from unittest.mock import create_autospec

    return create_autospec(PurchaseRepositoryABC)


# ---------------------------------------------------------------------------
# Spawning tasks for new purchases
# ---------------------------------------------------------------------------


# ──────────────────────────────────────────────────────────────────────────────
# _dispatch_pending_purchases — new pending purchases
# ──────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_dispatcher_spawns_task_for_each_new_pending_purchase_on_pending_purchases(
    repository: MagicMock,
) -> None:
    # Arrange
    pending_purchase = _make_purchase()
    session_factory, _ = _make_session_factory()
    repository.get_pending_purchases = AsyncMock(return_value=[pending_purchase])
    in_flight = InMemoryInFlightTracker()
    mock_task = MagicMock()
    spawn_task = MagicMock(return_value=mock_task)

    # Act
    await _dispatch_pending_purchases(
        repository=repository,
        db_session_factory=session_factory,
        in_flight=in_flight,
        spawn_task=spawn_task,
    )

    # Assert
    spawn_task.assert_called_once_with(pending_purchase.id)
    assert in_flight.contains(pending_purchase.id)


@pytest.mark.asyncio
async def test_dispatcher_spawns_tasks_for_multiple_new_purchases_on_multiple_pending_purchases(
    repository: MagicMock,
) -> None:
    # Arrange
    pending_purchases = [_make_purchase(purchase_id=f"p-{i}") for i in range(3)]
    session_factory, _ = _make_session_factory()
    repository.get_pending_purchases = AsyncMock(return_value=pending_purchases)
    in_flight = InMemoryInFlightTracker()
    spawn_task = MagicMock(side_effect=[MagicMock(name=f"task-{i}") for i in range(3)])

    # Act
    await _dispatch_pending_purchases(
        repository=repository,
        db_session_factory=session_factory,
        in_flight=in_flight,
        spawn_task=spawn_task,
    )

    # Assert
    assert spawn_task.call_count == 3
    assert all(in_flight.contains(p.id) for p in pending_purchases)


@pytest.mark.asyncio
async def test_dispatcher_does_nothing_on_no_pending_purchases(
    repository: MagicMock,
) -> None:
    # Arrange
    session_factory, _ = _make_session_factory()
    repository.get_pending_purchases = AsyncMock(return_value=[])
    spawn_task = MagicMock()

    # Act
    await _dispatch_pending_purchases(
        repository=repository,
        db_session_factory=session_factory,
        in_flight=InMemoryInFlightTracker(),
        spawn_task=spawn_task,
    )

    # Assert
    spawn_task.assert_not_called()


# ──────────────────────────────────────────────────────────────────────────────
# _dispatch_pending_purchases — skipping in-flight purchases
# ──────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_dispatcher_skips_purchases_already_in_flight_on_existing_in_flight(
    repository: MagicMock,
) -> None:
    """Purchases whose task is still running must not receive a duplicate task."""
    # Arrange
    pending_purchase = _make_purchase()
    session_factory, _ = _make_session_factory()
    repository.get_pending_purchases = AsyncMock(return_value=[pending_purchase])
    in_flight = InMemoryInFlightTracker()
    in_flight.add(pending_purchase.id, MagicMock(name="existing-task"))
    spawn_task = MagicMock()

    # Act
    await _dispatch_pending_purchases(
        repository=repository,
        db_session_factory=session_factory,
        in_flight=in_flight,
        spawn_task=spawn_task,
    )

    # Assert
    spawn_task.assert_not_called()
    assert in_flight.contains(pending_purchase.id)  # still tracked, unchanged


@pytest.mark.asyncio
async def test_dispatcher_spawns_only_for_new_purchases_in_mixed_batch_on_mixed_in_flight_and_new(
    repository: MagicMock,
) -> None:
    """With some in-flight and some new, only the new ones receive tasks."""
    # Arrange
    already_tracked = _make_purchase(purchase_id="in-flight-1")
    new_purchase = _make_purchase(purchase_id="new-1")
    session_factory, _ = _make_session_factory()
    repository.get_pending_purchases = AsyncMock(
        return_value=[already_tracked, new_purchase]
    )
    in_flight = InMemoryInFlightTracker()
    in_flight.add(already_tracked.id, MagicMock(name="existing-task"))
    new_task = MagicMock(name="new-task")
    spawn_task = MagicMock(return_value=new_task)

    # Act
    await _dispatch_pending_purchases(
        repository=repository,
        db_session_factory=session_factory,
        in_flight=in_flight,
        spawn_task=spawn_task,
    )

    # Assert
    spawn_task.assert_called_once_with(new_purchase.id)
    assert in_flight.contains(new_purchase.id)
    assert in_flight.contains(already_tracked.id)  # untouched
