from app.purchases.clients import MerchantsClient, OffersClient, UsersClient
from app.purchases.policies import (
    enforce_currency_eur,
    enforce_merchant_active,
    enforce_offer_available,
    enforce_purchase_ownership,
    enforce_purchase_view_ownership,
    enforce_user_active,
)
from app.purchases.repositories import PurchaseRepository
from app.purchases.services import PurchaseService


def get_purchase_repository() -> PurchaseRepository:
    return PurchaseRepository()


def get_purchase_service() -> PurchaseService:
    return PurchaseService(
        repository=get_purchase_repository(),
        users_client=UsersClient(),
        merchants_client=MerchantsClient(),
        offers_client=OffersClient(),
        enforce_purchase_ownership=enforce_purchase_ownership,
        enforce_user_active=enforce_user_active,
        enforce_merchant_active=enforce_merchant_active,
        enforce_offer_available=enforce_offer_available,
        enforce_currency_supported=enforce_currency_eur,
        enforce_purchase_view_ownership=enforce_purchase_view_ownership,
    )
