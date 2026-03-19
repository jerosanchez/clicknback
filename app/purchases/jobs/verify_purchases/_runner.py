"""Per-purchase verification runner.

Drives a single purchase through up to ``max_attempts`` verification rounds,
sleeping between soft failures and force-rejecting on exhaustion.  Opens a
fresh DB session per attempt; always removes itself from the in-flight
tracker on exit.  Calls into ``_processor.py`` once a disposition is decided.

Retry strategy
--------------
The runner uses a **fixed sleep interval** (``retry_interval_seconds``) between
consecutive soft-failure attempts.  This keeps the mental model simple and the
smoke-test timeline predictable, which is appropriate given the current
simulated bank gateway.

If ClickNBack integrates a real bank gateway in the future, consider migrating
to exponential-backoff-with-jitter so the gateway gets progressively more time
to recover between retries.  All changes are local to this file.

See ADR-017 for the full rationale and an upgrade path.
"""

import asyncio
from collections.abc import Callable
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.audit.services import AuditTrailABC
from app.core.broker import MessageBrokerABC
from app.core.logging import logger
from app.purchases.clients import CashbackClientABC, WalletsClientABC

# isort: off
# For some reason isort can't figure out the correct ordering of these imports,
# and it's easier to just disable it here than to fight with it.
from app.purchases.jobs.verify_purchases._processor import (
    _confirm_purchase,  # pyright: ignore[reportPrivateUsage]
    _reject_purchase,  # pyright: ignore[reportPrivateUsage]
)

# isort: on

from app.purchases.jobs.verify_purchases._in_flight_tracker import InFlightTrackerABC
from app.purchases.jobs.verify_purchases._verifiers import PurchaseVerifierABC
from app.purchases.repositories import PurchaseRepositoryABC
from app.purchases.schemas import PurchaseStatus


async def _run_verification_with_retry(  # pyright: ignore[reportUnusedFunction]
    *,
    purchase_id: str,
    repository: PurchaseRepositoryABC,
    wallets_client: WalletsClientABC,
    cashback_client: CashbackClientABC,
    audit_trail: AuditTrailABC,
    broker: MessageBrokerABC,
    db_session_factory: async_sessionmaker[AsyncSession],
    verifier: PurchaseVerifierABC,
    max_attempts: int,
    retry_interval_seconds: float,
    datetime_provider: Callable[[], datetime],
    in_flight: InFlightTrackerABC,
) -> None:
    """Per-purchase retry loop.

    Runs up to ``max_attempts`` discrete verification attempts, opening a fresh
    DB session per attempt so each attempt is an independent unit of work.
    Between attempts the coroutine sleeps for ``retry_interval_seconds`` —
    actual wall-clock time rather than a cycle count inferred from creation date.

    If the purchase is confirmed or hard-declined before retries are exhausted,
    the loop exits early.  If the purchase was already processed externally the
    loop exits without action.  On exhaustion without resolution the purchase is
    force-rejected.

    The coroutine always removes itself from ``in_flight`` on exit so the
    dispatcher can schedule a fresh task if the purchase somehow reappears.
    """
    try:
        for attempt in range(1, max_attempts + 1):
            async with db_session_factory() as db:
                purchase = await repository.get_by_id(db, purchase_id)

                if purchase is None or purchase.status != PurchaseStatus.PENDING.value:
                    logger.debug(
                        "verify_purchases: purchase no longer pending, stopping.",
                        extra={"purchase_id": purchase_id},
                    )
                    return

                now = datetime_provider()
                result = await verifier.verify(purchase, attempt)

                if result.disposition == "confirmed":
                    await _confirm_purchase(
                        purchase=purchase,
                        verified_at=now,
                        db=db,
                        repository=repository,
                        wallets_client=wallets_client,
                        cashback_client=cashback_client,
                        audit_trail=audit_trail,
                        broker=broker,
                    )
                    return

                if result.disposition == "rejected":
                    await _reject_purchase(
                        purchase=purchase,
                        reason=result.reason or "Verification declined.",
                        attempt=attempt,
                        failed_at=now,
                        db=db,
                        repository=repository,
                        wallets_client=wallets_client,
                        cashback_client=cashback_client,
                        audit_trail=audit_trail,
                        broker=broker,
                    )
                    return

            # "pending" — sleep before the next attempt (skip sleep after last attempt).
            logger.debug(
                "verify_purchases: attempt soft-failed, will retry.",
                extra={
                    "purchase_id": purchase_id,
                    "attempt": attempt,
                    "max_attempts": max_attempts,
                },
            )
            if attempt < max_attempts:
                await asyncio.sleep(retry_interval_seconds)

        # All attempts exhausted with only soft failures — force reject.
        reason = (
            f"Bank reconciliation failed: no matching bank movement found "
            f"after {max_attempts} verification attempt(s)."
        )
        async with db_session_factory() as db:
            purchase = await repository.get_by_id(db, purchase_id)
            if purchase is not None and purchase.status == PurchaseStatus.PENDING.value:
                now = datetime_provider()
                await _reject_purchase(
                    purchase=purchase,
                    reason=reason,
                    attempt=max_attempts,
                    failed_at=now,
                    db=db,
                    repository=repository,
                    wallets_client=wallets_client,
                    cashback_client=cashback_client,
                    audit_trail=audit_trail,
                    broker=broker,
                )
    finally:
        in_flight.discard(purchase_id)
