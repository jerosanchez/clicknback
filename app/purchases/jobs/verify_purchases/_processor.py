"""Purchase outcome processor.

Applies a resolved verification outcome: updates the purchase status in the
DB, moves the wallet balance, and publishes the domain event.

The status update, cashback transaction update, and wallet balance move are
committed atomically in a single transaction (see data-model §4.1 —
"Transactions ensure balance adjustments are atomic with status changes").
The domain event is published immediately after commit; audit logging is
handled by the audit module subscribing to those same domain events.
"""

from datetime import datetime
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.broker import MessageBrokerABC
from app.core.events.purchase_events import PurchaseConfirmed, PurchaseRejected
from app.core.logging import logger
from app.purchases.clients import CashbackClientABC, WalletsClientABC
from app.purchases.models import Purchase
from app.purchases.repositories import PurchaseRepositoryABC
from app.purchases.schemas import PurchaseStatus


async def _confirm_purchase(  # pyright: ignore[reportUnusedFunction]
    *,
    purchase: Purchase,
    verified_at: datetime,
    db: AsyncSession,
    repository: PurchaseRepositoryABC,
    wallets_client: WalletsClientABC,
    cashback_client: CashbackClientABC,
    broker: MessageBrokerABC,
) -> None:
    """Update status to confirmed, move pending balance to available, publish events."""
    await repository.update_status(db, purchase.id, PurchaseStatus.CONFIRMED.value)

    cashback_amount: Decimal = purchase.cashback_amount
    if cashback_amount > Decimal("0"):
        await cashback_client.confirm(db, purchase.id)
        await wallets_client.confirm_pending(db, purchase.user_id, cashback_amount)

    await db.commit()

    await broker.publish(
        PurchaseConfirmed(
            purchase_id=purchase.id,
            user_id=purchase.user_id,
            merchant_id=purchase.merchant_id,
            amount=purchase.amount,
            currency=purchase.currency,
            cashback_amount=cashback_amount,
            verified_at=verified_at,
        )
    )

    logger.info(
        "verify_purchases: purchase confirmed.",
        extra={"purchase_id": purchase.id, "merchant_id": purchase.merchant_id},
    )


async def _reject_purchase(  # pyright: ignore[reportUnusedFunction]
    *,
    purchase: Purchase,
    reason: str,
    attempt: int,
    failed_at: datetime,
    db: AsyncSession,
    repository: PurchaseRepositoryABC,
    wallets_client: WalletsClientABC,
    cashback_client: CashbackClientABC,
    broker: MessageBrokerABC,
) -> None:
    """Update status to rejected, remove pending balance, publish events."""
    await repository.update_status(db, purchase.id, PurchaseStatus.REJECTED.value)

    cashback_amount: Decimal = purchase.cashback_amount
    if cashback_amount > Decimal("0"):
        await cashback_client.reverse(db, purchase.id)
        await wallets_client.reverse_pending(db, purchase.user_id, cashback_amount)

    await db.commit()

    await broker.publish(
        PurchaseRejected(
            purchase_id=purchase.id,
            user_id=purchase.user_id,
            merchant_id=purchase.merchant_id,
            amount=purchase.amount,
            currency=purchase.currency,
            failed_at=failed_at,
            reason=reason,
        )
    )

    logger.info(
        "verify_purchases: purchase rejected.",
        extra={"purchase_id": purchase.id, "merchant_id": purchase.merchant_id},
    )
