from app.merchants.repository import MerchantRepository
from app.offers.policies import (
    enforce_cashback_value_validity,
    enforce_date_range_validity,
    enforce_merchant_is_active,
    enforce_monthly_cap_validity,
    enforce_no_active_offer_exists,
    enforce_offer_merchant_visibility,
    enforce_offer_visibility,
)
from app.offers.repositories import OfferRepository
from app.offers.services import OfferService


def get_offer_repository() -> OfferRepository:
    return OfferRepository()


def get_merchant_repository_for_offers() -> MerchantRepository:
    return MerchantRepository()


def get_offer_service() -> OfferService:
    return OfferService(
        enforce_cashback_value_validity=enforce_cashback_value_validity,
        enforce_date_range_validity=enforce_date_range_validity,
        enforce_monthly_cap_validity=enforce_monthly_cap_validity,
        enforce_merchant_is_active=enforce_merchant_is_active,
        enforce_no_active_offer_exists=enforce_no_active_offer_exists,
        enforce_offer_visibility=enforce_offer_visibility,
        enforce_offer_merchant_visibility=enforce_offer_merchant_visibility,
        offer_repository=get_offer_repository(),
        merchant_repository=get_merchant_repository_for_offers(),
    )
