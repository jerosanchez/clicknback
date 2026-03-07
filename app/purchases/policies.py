from app.purchases.clients import MerchantDTO, OfferDTO, UserDTO
from app.purchases.exceptions import (
    MerchantInactiveException,
    MerchantNotFoundException,
    OfferNotAvailableException,
    PurchaseOwnershipViolationException,
    UnsupportedCurrencyException,
    UserInactiveException,
    UserNotFoundException,
)

_SUPPORTED_CURRENCIES: frozenset[str] = frozenset({"EUR"})


def enforce_purchase_ownership(current_user_id: str, requested_user_id: str) -> None:
    """Raise if the authenticated user is not the owner of the purchase being ingested."""
    if current_user_id != requested_user_id:
        raise PurchaseOwnershipViolationException(current_user_id, requested_user_id)


def enforce_user_active(user: UserDTO | None, user_id: str) -> None:
    """Raise if the user does not exist or is not active."""
    if user is None:
        raise UserNotFoundException(user_id)
    if not user.active:
        raise UserInactiveException(user_id)


def enforce_merchant_active(merchant: MerchantDTO | None, merchant_id: str) -> None:
    """Raise if the merchant does not exist or is not active."""
    if merchant is None:
        raise MerchantNotFoundException(merchant_id)
    if not merchant.active:
        raise MerchantInactiveException(merchant_id)


def enforce_offer_available(offer: OfferDTO | None, merchant_id: str) -> None:
    """Raise if no active, date-valid offer exists for the merchant."""
    if offer is None:
        raise OfferNotAvailableException(merchant_id)


def enforce_currency_eur(currency: str) -> None:
    """Raise if the currency is not among the supported currencies (currently EUR only)."""
    if currency.upper() not in _SUPPORTED_CURRENCIES:
        raise UnsupportedCurrencyException(currency)
