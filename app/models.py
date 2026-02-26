# Import all model classes here so Alembic can discover them
# See alembic/env.py for reference.
from app.merchants.models import Merchant
from app.users.models import User

__all__ = ["User", "Merchant"]
