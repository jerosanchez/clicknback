"""Enums for the audit trail: actor types, outcomes, and auditable actions."""

import enum


class AuditActorType(str, enum.Enum):
    """Who initiated the operation."""

    system = "system"  # background job / event handler — no human involved
    admin = "admin"  # authenticated admin user
    user = "user"  # authenticated regular user


class AuditOutcome(str, enum.Enum):
    success = "success"
    failure = "failure"


class AuditAction(str, enum.Enum):
    """Exhaustive list of auditable operations.

    Add a new member here when implementing a new critical operation.
    Maximum length is 64 characters (enforced by the DB column).
    """

    PURCHASE_CONFIRMED = "PURCHASE_CONFIRMED"
    PURCHASE_REJECTED = "PURCHASE_REJECTED"
    CASHBACK_CREDITED = "CASHBACK_CREDITED"
    WITHDRAWAL_REQUESTED = "WITHDRAWAL_REQUESTED"
    WITHDRAWAL_PROCESSED = "WITHDRAWAL_PROCESSED"
    PURCHASE_REVERSED = "PURCHASE_REVERSED"
    MERCHANT_ACTIVATED = "MERCHANT_ACTIVATED"
    OFFER_ACTIVATED = "OFFER_ACTIVATED"
