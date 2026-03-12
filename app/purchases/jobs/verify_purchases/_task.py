"""Composition root for the purchase verification background job.

Wires the Dispatcher, Runner, Processor, Verifier strategy, and InFlight
tracker together and returns a zero-argument ``ScheduledTask`` for the
scheduler.  This is the only file that imports from all other modules in
the package.

See ADR-016 for the full architectural rationale and a guide on applying
this pattern to other background jobs.
"""

import asyncio
from collections.abc import Callable
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.audit.services import AuditTrailABC
from app.core.broker import MessageBrokerABC
from app.core.scheduler import ScheduledTask
from app.purchases.repositories import PurchaseRepositoryABC

from ._dispatcher import _dispatch_pending_purchases
from ._in_flight_tracker import InFlightTrackerABC, InMemoryInFlightTracker
from ._runner import _run_verification_with_retry
from ._verifiers import PurchaseVerifierABC


def make_verify_purchases_task(
    *,
    repository: PurchaseRepositoryABC,
    audit_trail: AuditTrailABC,
    broker: MessageBrokerABC,
    db_session_factory: async_sessionmaker[AsyncSession],
    verifier: PurchaseVerifierABC,
    max_attempts: int,
    retry_interval_seconds: float,
    datetime_provider: Callable[[], datetime],
) -> ScheduledTask:
    """Return a ScheduledTask (dispatcher) that discovers and verifies pending purchases.

    On each invocation the dispatcher scans for pending purchases without an
    active task and spawns one ``asyncio.Task`` per purchase.  Each per-purchase
    task runs ``_run_verification_with_retry`` independently, sleeping
    ``retry_interval_seconds`` between attempts — giving each purchase its own
    isolated retry lifecycle rather than a shared batch cycle.

    Args:
        repository:              Async purchase repository.
        audit_trail:             Audit trail service for recording outcomes.
        broker:                  Message broker for publishing domain events.
        db_session_factory:      ``AsyncSessionLocal`` factory; each attempt
                                 opens its own session.
        verifier:                Verification strategy — decides the outcome of
                                 each individual attempt.  Swap implementations
                                 to connect a real bank gateway.
        max_attempts:            Maximum attempts per purchase before
                                 force-rejecting.
        retry_interval_seconds:  Sleep between consecutive attempts on the same
                                 purchase.
        datetime_provider:       Returns the current UTC datetime; injected at
                                 compose time, override in tests to freeze time.
    """
    in_flight: InFlightTrackerABC = InMemoryInFlightTracker()

    def _spawn(purchase_id: str) -> asyncio.Task[None]:
        return asyncio.create_task(
            _run_verification_with_retry(
                purchase_id=purchase_id,
                repository=repository,
                audit_trail=audit_trail,
                broker=broker,
                db_session_factory=db_session_factory,
                verifier=verifier,
                max_attempts=max_attempts,
                retry_interval_seconds=retry_interval_seconds,
                datetime_provider=datetime_provider,
                in_flight=in_flight,
            ),
            name=f"verify_purchase_{purchase_id}",
        )

    async def task() -> None:
        await _dispatch_pending_purchases(
            repository=repository,
            db_session_factory=db_session_factory,
            in_flight=in_flight,
            spawn_task=_spawn,
        )

    return task
