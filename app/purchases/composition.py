from app.purchases.repositories import PurchaseRepository
from app.purchases.services import PurchaseService


def get_purchase_repository() -> PurchaseRepository:
    return PurchaseRepository()


def get_purchase_service() -> PurchaseService:
    return PurchaseService(get_purchase_repository())
