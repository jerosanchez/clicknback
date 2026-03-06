from abc import ABC

from app.purchases.models import Purchase  # noqa: F401


class PurchaseRepositoryABC(ABC):
    pass


class PurchaseRepository(PurchaseRepositoryABC):
    pass
