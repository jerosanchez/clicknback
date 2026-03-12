from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


@dataclass(frozen=True)
class PurchaseConfirmed:
    """Published by the bank-verification background job when a pending
    purchase is successfully matched to a bank movement.

    Expected subscribers:
    - Cashback service: calculates and credits cashback to the user's wallet.
    - Notification service (future): sends confirmation email/push to the user.

    Fields:
        purchase_id:  Internal UUID of the confirmed purchase.
        user_id:      UUID of the user who ingested the purchase.
        merchant_id:  UUID of the merchant linked to the purchase.
        amount:       Original purchase amount (Decimal, EUR).
        verified_at:  UTC timestamp when verification succeeded.
    """

    purchase_id: str
    user_id: str
    merchant_id: str
    amount: Decimal
    verified_at: datetime


@dataclass(frozen=True)
class PurchaseRejected:
    """Published by the bank-verification background job when verification
    fails after exhausting all retry attempts.

    Expected subscribers:
    - Purchase service: transitions purchase status to ``rejected``.
    - Notification service (future): informs the user that no cashback will
      be awarded for this purchase.

    Fields:
        purchase_id:  Internal UUID of the rejected purchase.
        user_id:      UUID of the user who ingested the purchase.
        merchant_id:  UUID of the merchant linked to the purchase.
        amount:       Original purchase amount (Decimal, EUR).
        failed_at:    UTC timestamp when the final retry was exhausted.
        reason:       Human-readable explanation of the rejection.
    """

    purchase_id: str
    user_id: str
    merchant_id: str
    amount: Decimal
    failed_at: datetime
    reason: str
