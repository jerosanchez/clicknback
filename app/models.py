# Import all model classes here so Alembic can discover them
# See alembic/env.py for reference.
from app.cashback.models import CashbackTransaction
from app.core.audit import AuditLog
from app.merchants.models import Merchant
from app.offers.models import Offer
from app.purchases.models import Purchase
from app.users.models import User
from app.wallets.models import Wallet

__all__ = [
    "AuditLog",
    "CashbackTransaction",
    "User",
    "Merchant",
    "Offer",
    "Purchase",
    "Wallet",
]
