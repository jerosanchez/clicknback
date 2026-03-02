from app.offers.repositories import OfferRepository
from app.offers.services import OfferService


def get_offer_repository() -> OfferRepository:
    return OfferRepository()


def get_offer_service() -> OfferService:
    return OfferService(get_offer_repository())
