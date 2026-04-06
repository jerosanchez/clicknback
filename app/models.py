# Import all model classes here so Alembic can discover them
# See alembic/env.py for reference.
from app.auth.models import RefreshToken
from app.cashback.models import CashbackTransaction
from app.core.audit import AuditLog
from app.feature_flags.models import FeatureFlag
from app.merchants.models import Merchant
from app.offers.models import Offer
from app.purchases.models import Purchase
from app.users.models import User
from app.wallets.models import Wallet

__all__ = [
    "AuditLog",
    "CashbackTransaction",
    "FeatureFlag",
    "User",
    "Merchant",
    "Offer",
    "Purchase",
    "Wallet",
    "RefreshToken",
]
