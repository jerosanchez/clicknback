# Import all model classes here so Alembic can discover them
# See alembic/env.py for reference.
from app.merchants.models import Merchant
from app.offers.models import Offer
from app.purchases.models import Purchase
from app.users.models import User

__all__ = ["User", "Merchant", "Offer", "Purchase"]
