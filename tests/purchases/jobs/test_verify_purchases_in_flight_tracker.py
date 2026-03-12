"""Unit tests for InMemoryInFlightTracker.

Covers the full public contract defined by ``InFlightTrackerABC`` so that a
future ``RedisInFlightTracker`` can reuse this same suite with minimal changes.
An additional test verifies the internal task-reference storage, which is
specific to the in-memory implementation and useful for graceful shutdown.
"""

import asyncio
from unittest.mock import MagicMock

from app.purchases.jobs.verify_purchases._in_flight_tracker import (
    InMemoryInFlightTracker,
)


def _make_task() -> asyncio.Task[None]:
    return MagicMock(spec=asyncio.Task)


_PURCHASE_ID_1: str = "purchase-1"
_PURCHASE_ID_2: str = "purchase-2"

# ──────────────────────────────────────────────────────────────────────────────
# InMemoryInFlightTracker — initial state
# ──────────────────────────────────────────────────────────────────────────────


def test_tracker_is_empty_on_creation() -> None:
    # Arrange
    tracker = InMemoryInFlightTracker()

    # Act
    count = tracker.count()

    # Assert
    assert count == 0


def test_tracker_contains_returns_false_on_unknown_id() -> None:
    # Arrange
    tracker = InMemoryInFlightTracker()

    # Act
    result = tracker.contains(_PURCHASE_ID_1)

    # Assert
    assert not result


# ──────────────────────────────────────────────────────────────────────────────
# add
# ──────────────────────────────────────────────────────────────────────────────


def test_tracker_add_makes_contains_return_true_on_add() -> None:
    # Arrange
    tracker = InMemoryInFlightTracker()

    # Act
    tracker.add(_PURCHASE_ID_1, _make_task())

    # Assert
    assert tracker.contains(_PURCHASE_ID_1)


def test_tracker_add_increments_count_on_multiple_adds() -> None:
    # Arrange
    tracker = InMemoryInFlightTracker()

    # Act
    tracker.add(_PURCHASE_ID_1, _make_task())
    tracker.add(_PURCHASE_ID_2, _make_task())

    # Assert
    assert tracker.count() == 2


def test_tracker_add_stores_the_exact_task_reference_on_task_storage() -> None:
    """The in-memory implementation stores the task object for potential graceful shutdown."""
    # Arrange
    tracker = InMemoryInFlightTracker()
    task = _make_task()

    # Act
    tracker.add(_PURCHASE_ID_1, task)

    # Assert
    assert tracker._tasks[_PURCHASE_ID_1] is task  # pyright: ignore[reportPrivateUsage]


def test_tracker_add_overwrites_previous_task_for_same_id_on_overwrite() -> None:
    # Arrange
    tracker = InMemoryInFlightTracker()
    task_a = _make_task()
    task_b = _make_task()

    # Act
    tracker.add(_PURCHASE_ID_1, task_a)
    tracker.add(_PURCHASE_ID_1, task_b)

    # Assert
    assert tracker.count() == 1
    assert (
        tracker._tasks[_PURCHASE_ID_1] is task_b  # pyright: ignore[reportPrivateUsage]
    )


# ──────────────────────────────────────────────────────────────────────────────
# discard
# ──────────────────────────────────────────────────────────────────────────────


def test_tracker_discard_removes_tracked_purchase_on_discard() -> None:
    # Arrange
    tracker = InMemoryInFlightTracker()
    tracker.add(_PURCHASE_ID_1, _make_task())

    # Act
    tracker.discard(_PURCHASE_ID_1)

    # Assert
    assert not tracker.contains(_PURCHASE_ID_1)


def test_tracker_discard_decrements_count_on_discard() -> None:
    # Arrange
    tracker = InMemoryInFlightTracker()
    tracker.add(_PURCHASE_ID_1, _make_task())
    tracker.add(_PURCHASE_ID_2, _make_task())

    # Act
    tracker.discard(_PURCHASE_ID_1)

    # Assert
    assert tracker.count() == 1


def test_tracker_discard_is_noop_for_unknown_id_on_noop() -> None:
    """discard must not raise when the purchase is not tracked."""
    # Arrange

    tracker = InMemoryInFlightTracker()
    # Act

    tracker.discard("nonexistent")  # must not raise
    # Assert
    # No exception means pass


def test_tracker_discard_does_not_affect_other_ids_on_selective_discard() -> None:
    # Arrange
    tracker = InMemoryInFlightTracker()
    tracker.add(_PURCHASE_ID_1, _make_task())
    tracker.add(_PURCHASE_ID_2, _make_task())

    # Act
    tracker.discard(_PURCHASE_ID_1)

    # Assert
    assert tracker.contains(_PURCHASE_ID_2)
