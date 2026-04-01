"""Fan-out dispatcher for the purchase verification job.

Scans for pending purchases on each scheduler tick and spawns one
``asyncio.Task`` per new purchase via an injectable ``spawn_task`` callable.
Purchases already tracked in the in-flight tracker are skipped.

The ``spawn_task`` callable is injected by the task builder, keeping this
module decoupled from the runner and trivially testable without real tasks.

Auto-confirmation can be disabled via feature flags on a per-user or
per-merchant basis. Purchases with auto-confirmation disabled remain in
pending state and can be manually confirmed later.
"""

from collections.abc import Callable
from typing import TYPE_CHECKING

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.logging import logger
from app.purchases.clients import FeatureFlagClientABC
from app.purchases.repositories import PurchaseRepositoryABC

from ._in_flight_tracker import InFlightTrackerABC

if TYPE_CHECKING:
    import asyncio


async def _dispatch_pending_purchases(  # pyright: ignore[reportUnusedFunction]
    *,
    repository: PurchaseRepositoryABC,
    db_session_factory: async_sessionmaker[AsyncSession],
    in_flight: InFlightTrackerABC,
    feature_flag_client: FeatureFlagClientABC,
    spawn_task: Callable[[str], "asyncio.Task[None]"],
) -> None:
    """Scan for pending purchases and spawn a per-purchase task for each new one.

    Purchases already tracked in ``in_flight`` are skipped — their retry loop
    is still running.  Only new purchases (or ones whose prior task has finished
    and cleaned itself up) receive a fresh task.

    Purchases with auto-confirmation disabled (via feature flag) are also
    skipped and remain in pending state for manual confirmation.

    ``spawn_task`` is injectable so the dispatcher can be tested without
    launching real asyncio tasks.
    """
    async with db_session_factory() as db:
        pending = await repository.get_pending_purchases(db)

    logger.info(
        "verify_purchases: dispatcher tick.",
        extra={
            "pending_count": len(pending) if pending else 0,
            "in_flight_count": in_flight.count(),
        },
    )

    if not pending:
        return

    new_purchases = [p for p in pending if not in_flight.contains(p.id)]

    if not new_purchases:
        logger.info(
            "verify_purchases: all pending purchases already in-flight.",
            extra={"in_flight_count": in_flight.count()},
        )
        return

    # Filter out purchases with auto-confirmation disabled via feature flag
    async with db_session_factory() as db:
        eligible_purchases, skipped_count = (
            await feature_flag_client.filter_eligible_purchases(db, new_purchases)
        )

    for purchase in eligible_purchases:
        in_flight.add(purchase.id, spawn_task(purchase.id))

    if not eligible_purchases:
        message_extra = {"in_flight_count": in_flight.count()}
        if skipped_count > 0:
            message_extra["skipped_count"] = skipped_count
        logger.info(
            "verify_purchases: no eligible purchases to verify.",
            extra=message_extra,
        )
        return

    logger.info(
        "verify_purchases: dispatched per-purchase verification tasks.",
        extra={
            "spawned_tasks": len(eligible_purchases),
            "total_in_flight": in_flight.count(),
            "skipped_count": skipped_count if skipped_count > 0 else 0,
        },
    )
