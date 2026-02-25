# merchants service stub
import uuid
from typing import Any

from sqlalchemy.orm import Session

from app.merchants.models import Merchant
from app.merchants.repository import MerchantRepository


class MerchantService:
    def __init__(self, repository: MerchantRepository):
        self.repository = repository

    def create_merchant(self, merchant_data: dict[str, Any], db: Session) -> Merchant:
        new_merchant = Merchant(
            id=uuid.uuid4(),
            name=merchant_data["name"],
            default_cashback_percentage=merchant_data["default_cashback_percentage"],
            active=merchant_data["active"],
        )

        return self.repository.add_merchant(db, new_merchant)
