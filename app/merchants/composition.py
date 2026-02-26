from app.merchants.policies import enforce_cashback_percentage_validity
from app.merchants.repository import MerchantRepository
from app.merchants.services import MerchantService


def get_enforce_cashback_percentage_validity():
    return enforce_cashback_percentage_validity


def get_merchant_repository():
    return MerchantRepository()


def get_merchant_service():
    return MerchantService(
        get_enforce_cashback_percentage_validity(), get_merchant_repository()
    )
