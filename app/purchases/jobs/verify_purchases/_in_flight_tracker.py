"""In-flight tracker for background processing tasks.

``InFlightTrackerABC`` tracks which purchases are currently being verified
so the dispatcher never spawns a duplicate task.  ``InMemoryInFlightTracker``
is safe within a single asyncio event loop.  Replace it with a
``RedisInFlightTracker`` behind the same interface for multi-process
deployments.  See ADR-016 for rationale.
"""

import asyncio
from abc import ABC, abstractmethod


class InFlightTrackerABC(ABC):
    """Contract for tracking which purchases are currently being processed.

    Implementations must be safe to call from within the asyncio event loop.
    """

    @abstractmethod
    def add(self, purchase_id: str, task: asyncio.Task[None]) -> None:
        """Mark ``purchase_id`` as in-flight, associating it with ``task``."""

    @abstractmethod
    def discard(self, purchase_id: str) -> None:
        """Remove ``purchase_id`` from the tracker.  No-op if not present."""

    @abstractmethod
    def contains(self, purchase_id: str) -> bool:
        """Return ``True`` if ``purchase_id`` is currently in-flight."""

    @abstractmethod
    def count(self) -> int:
        """Return the number of currently in-flight purchases."""


class InMemoryInFlightTracker(InFlightTrackerABC):
    """In-process tracker backed by a plain Python dictionary.

    Safe within a single asyncio event loop (single-threaded; no locking
    needed).  Stores the ``asyncio.Task`` reference to support future
    graceful-shutdown logic (awaiting all in-flight tasks before stopping).
    """

    def __init__(self) -> None:
        self._tasks: dict[str, asyncio.Task[None]] = {}

    def add(self, purchase_id: str, task: asyncio.Task[None]) -> None:
        self._tasks[purchase_id] = task

    def discard(self, purchase_id: str) -> None:
        self._tasks.pop(purchase_id, None)

    def contains(self, purchase_id: str) -> bool:
        return purchase_id in self._tasks

    def count(self) -> int:
        return len(self._tasks)
