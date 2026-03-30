from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


@dataclass(frozen=True)
class PurchaseConfirmed:
    """Published by the bank-verification background job when a pending
    purchase is successfully matched to a bank movement.

    Expected subscribers:
    - Audit module: records a PURCHASE_CONFIRMED audit log entry.
    - Notification service (future): sends confirmation email/push to the user.

    Fields:
        purchase_id:    Internal UUID of the confirmed purchase.
        user_id:        UUID of the user who ingested the purchase.
        merchant_id:    UUID of the merchant linked to the purchase.
        amount:         Original purchase amount (Decimal, EUR).
        currency:       ISO 4217 currency code (e.g. "EUR").
        cashback_amount: Cashback amount credited to the user's wallet (Decimal).
        verified_at:    UTC timestamp when verification succeeded.
    """

    purchase_id: str
    user_id: str
    merchant_id: str
    amount: Decimal
    currency: str
    cashback_amount: Decimal
    verified_at: datetime


@dataclass(frozen=True)
class PurchaseRejected:
    """Published by the bank-verification background job when verification
    fails after exhausting all retry attempts.

    Expected subscribers:
    - Audit module: records a PURCHASE_REJECTED audit log entry.
    - Notification service (future): informs the user that no cashback will
      be awarded for this purchase.

    Fields:
        purchase_id:  Internal UUID of the rejected purchase.
        user_id:      UUID of the user who ingested the purchase.
        merchant_id:  UUID of the merchant linked to the purchase.
        amount:       Original purchase amount (Decimal, EUR).
        currency:     ISO 4217 currency code (e.g. "EUR").
        failed_at:    UTC timestamp when the final retry was exhausted.
        reason:       Human-readable explanation of the rejection.
    """

    purchase_id: str
    user_id: str
    merchant_id: str
    amount: Decimal
    currency: str
    failed_at: datetime
    reason: str


@dataclass(frozen=True)
class PurchaseReversed:
    """Published when an admin reverses a purchase via the API.

    Expected subscribers:
    - Audit module: records a PURCHASE_REVERSED audit log entry.
    - Notification service (future): informs the user their cashback was
      revoked.

    Fields:
        purchase_id:  Internal UUID of the reversed purchase.
        user_id:      UUID of the user who originally ingested the purchase.
        admin_id:     UUID of the admin who performed the reversal.
        merchant_id:  UUID of the merchant linked to the purchase.
        amount:       Original purchase amount (Decimal, EUR).
        currency:     ISO 4217 currency code (e.g. "EUR").
        prior_status: Purchase status immediately before the reversal.
    """

    purchase_id: str
    user_id: str
    admin_id: str
    merchant_id: str
    amount: Decimal
    currency: str
    prior_status: str


@dataclass(frozen=True)
class PurchaseConfirmedByAdmin:
    """Published when an admin manually confirms a pending purchase via the API.

    Expected subscribers:
    - Audit module: records a PURCHASE_CONFIRMED_BY_ADMIN audit log entry,
      capturing the admin's user ID to distinguish from automatic confirmation.
    - Notification service (future): sends confirmation email/push to the user.

    Fields:
        purchase_id:    Internal UUID of the confirmed purchase.
        user_id:        UUID of the user who ingested the purchase.
        admin_id:       UUID of the admin who performed the confirmation.
        merchant_id:    UUID of the merchant linked to the purchase.
        amount:         Original purchase amount (Decimal, EUR).
        currency:       ISO 4217 currency code (e.g. "EUR").
        cashback_amount: Cashback amount credited to the user's wallet (Decimal).
        confirmed_at:   UTC timestamp when the admin confirmed the purchase.
    """

    purchase_id: str
    user_id: str
    admin_id: str
    merchant_id: str
    amount: Decimal
    currency: str
    cashback_amount: Decimal
    confirmed_at: datetime
