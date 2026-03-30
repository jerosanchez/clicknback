"""Core purchase confirmation state transition.

Encapsulates the atomic state changes that confirm a purchase:

1. Update purchase status to CONFIRMED.
2. Confirm the backing cashback transaction record.
3. Move the cashback amount from pending_balance to available_balance.

This is the single source of truth for the confirmation state transition.
Callers (``PurchaseService`` and the background job processor) are responsible
for committing the transaction and publishing domain events after this function
returns.

Having this logic in one place prevents the two confirmation paths from silently
diverging — the class of bug described in the post that motivated this extraction.
"""

from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.purchases.clients import CashbackClientABC, WalletsClientABC
from app.purchases.models import Purchase
from app.purchases.repositories import PurchaseRepositoryABC
from app.purchases.schemas import PurchaseStatus


async def apply_purchase_confirmation(
    *,
    purchase: Purchase,
    db: AsyncSession,
    repository: PurchaseRepositoryABC,
    cashback_client: CashbackClientABC,
    wallets_client: WalletsClientABC,
) -> Purchase:
    """Apply the confirmation state transition to a purchase.

    Updates the purchase status to CONFIRMED, confirms the backing cashback
    transaction record, and moves the cashback amount from ``pending_balance``
    to ``available_balance``.

    When ``cashback_amount`` is zero no cashback or wallet calls are made.

    Callers must commit the session and publish domain events after this
    function returns.
    """
    confirmed = await repository.update_status(
        db, purchase.id, PurchaseStatus.CONFIRMED.value
    )

    if purchase.cashback_amount > Decimal("0"):
        await cashback_client.confirm(db, purchase.id)
        await wallets_client.confirm_pending(
            db, purchase.user_id, purchase.cashback_amount
        )

    return confirmed  # type: ignore[return-value]
