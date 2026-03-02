from app.offers.repositories import OfferRepositoryABC


class OfferService:
    def __init__(self, repository: OfferRepositoryABC):
        self.repository = repository
