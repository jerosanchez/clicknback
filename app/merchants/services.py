# merchants service stub
import uuid
from typing import Any, Callable

from sqlalchemy.orm import Session

from app.merchants.models import Merchant
from app.merchants.repository import MerchantRepositoryABC


class MerchantService:
    def __init__(
        self,
        enforce_cashback_percentage_validity: Callable[[float], None],
        merchant_repository: MerchantRepositoryABC,
    ):
        self.enforce_cashback_percentage_validity = enforce_cashback_percentage_validity
        self.merchant_repository = merchant_repository

    def create_merchant(self, merchant_data: dict[str, Any], db: Session) -> Merchant:
        default_cashback_percentage = merchant_data.get(
            "default_cashback_percentage", 0
        )
        self.enforce_cashback_percentage_validity(default_cashback_percentage)

        new_merchant = Merchant(
            id=uuid.uuid4(),
            name=merchant_data["name"],
            default_cashback_percentage=merchant_data["default_cashback_percentage"],
            active=merchant_data["active"],
        )

        return self.merchant_repository.add_merchant(db, new_merchant)
