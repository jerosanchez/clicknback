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

from app.core.broker import MessageBrokerABC
from app.core.scheduler import ScheduledTask
from app.purchases.clients import (
    CashbackClientABC,
    FeatureFlagClientABC,
    WalletsClientABC,
)
from app.purchases.repositories import PurchaseRepositoryABC

from ._dispatcher import (
    _dispatch_pending_purchases,  # pyright: ignore[reportPrivateUsage]
)
from ._in_flight_tracker import InFlightTrackerABC, InMemoryInFlightTracker
from ._runner import _run_verification_with_retry  # pyright: ignore[reportPrivateUsage]
from ._verifiers import PurchaseVerifierABC


def make_verify_purchases_task(
    *,
    repository: PurchaseRepositoryABC,
    wallets_client: WalletsClientABC,
    cashback_client: CashbackClientABC,
    broker: MessageBrokerABC,
    db_session_factory: async_sessionmaker[AsyncSession],
    feature_flag_client: FeatureFlagClientABC,
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
    """
    in_flight: InFlightTrackerABC = InMemoryInFlightTracker()

    def _spawn(purchase_id: str) -> asyncio.Task[None]:
        return asyncio.create_task(
            _run_verification_with_retry(
                purchase_id=purchase_id,
                repository=repository,
                wallets_client=wallets_client,
                cashback_client=cashback_client,
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
            feature_flag_client=feature_flag_client,
            spawn_task=_spawn,
        )

    return task
