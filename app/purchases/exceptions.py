from datetime import datetime
from decimal import Decimal


class DuplicatePurchaseException(Exception):
    def __init__(self, external_id: str, created_at: datetime, amount: Decimal):
        super().__init__(
            f"A purchase with external ID '{external_id}' has already been processed."
        )
        self.external_id = external_id
        self.created_at = created_at
        self.amount = amount


class UserNotFoundException(Exception):
    def __init__(self, user_id: str):
        super().__init__(f"User with ID '{user_id}' does not exist.")
        self.user_id = user_id


class UserInactiveException(Exception):
    def __init__(self, user_id: str):
        super().__init__(f"User with ID '{user_id}' is inactive.")
        self.user_id = user_id


class MerchantNotFoundException(Exception):
    def __init__(self, merchant_id: str):
        super().__init__(f"Merchant with ID '{merchant_id}' does not exist.")
        self.merchant_id = merchant_id


class MerchantInactiveException(Exception):
    def __init__(self, merchant_id: str):
        super().__init__(f"Merchant with ID '{merchant_id}' is inactive.")
        self.merchant_id = merchant_id


class OfferNotAvailableException(Exception):
    """No active, date-valid offer exists for the merchant.

    Covers three root causes: no offer, offer inactive, or offer outside its
    valid date range (expired or not yet started).
    """

    def __init__(self, merchant_id: str):
        super().__init__(f"No active offer is available for merchant '{merchant_id}'.")
        self.merchant_id = merchant_id


class UnsupportedCurrencyException(Exception):
    def __init__(self, currency: str):
        super().__init__(
            f"Currency '{currency}' is not supported. Only EUR is accepted."
        )
        self.currency = currency


class PurchaseOwnershipViolationException(Exception):
    """The authenticated user is not the owner of the purchase being ingested."""

    def __init__(self, current_user_id: str, requested_user_id: str):
        super().__init__(
            f"User '{current_user_id}' is not allowed to ingest purchases for user '{requested_user_id}'."
        )
        self.current_user_id = current_user_id
        self.requested_user_id = requested_user_id


class InvalidPurchaseStatusException(Exception):
    def __init__(self, status: str):
        super().__init__(
            f"'{status}' is not a valid purchase status. "
            "Allowed values: pending, confirmed, reversed."
        )
        self.status = status


class PurchaseNotFoundException(Exception):
    def __init__(self, purchase_id: str):
        super().__init__(f"Purchase with ID '{purchase_id}' does not exist.")
        self.purchase_id = purchase_id


class PurchaseViewForbiddenException(Exception):
    """The authenticated user is not the owner of the purchase being viewed."""

    def __init__(self, purchase_id: str, resource_owner_id: str, current_user_id: str):
        super().__init__(
            f"User '{current_user_id}' does not have permission to view purchase '{purchase_id}'."
        )
        self.purchase_id = purchase_id
        self.resource_owner_id = resource_owner_id
        self.current_user_id = current_user_id
