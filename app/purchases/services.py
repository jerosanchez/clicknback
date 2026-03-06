from app.purchases.repositories import PurchaseRepositoryABC


class PurchaseService:
    def __init__(self, repository: PurchaseRepositoryABC):
        self.repository = repository
