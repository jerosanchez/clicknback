from .repository import MerchantRepository
from .services import MerchantService


def get_merchant_repository():
    return MerchantRepository()


def get_merchant_service():
    return MerchantService(get_merchant_repository())
