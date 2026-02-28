# merchants service stub
from typing import Any, Callable

from sqlalchemy.orm import Session

from app.core.logging import logger
from app.merchants.exceptions import (
    MerchantNameAlreadyExistsException,
    MerchantNotFoundException,
)
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
        default_cashback_percentage = merchant_data["default_cashback_percentage"]
        name = merchant_data["name"]
        active = merchant_data["active"]

        self.enforce_cashback_percentage_validity(default_cashback_percentage)

        self._enforce_merchant_name_uniqueness(name, db)

        new_merchant = Merchant(
            name=name,
            default_cashback_percentage=default_cashback_percentage,
            active=active,
        )

        return self.merchant_repository.add_merchant(db, new_merchant)

    def list_merchants(
        self,
        page: int,
        page_size: int,
        active: bool | None,
        db: Session,
    ) -> tuple[list[Merchant], int]:
        return self.merchant_repository.list_merchants(db, page, page_size, active)

    def set_merchant_status(
        self, merchant_id: str, active: bool, db: Session
    ) -> Merchant:
        merchant = self.merchant_repository.get_merchant_by_id(db, merchant_id)
        if merchant is None:
            logger.debug(
                "Merchant not found for status update.",
                extra={"merchant_id": merchant_id},
            )
            raise MerchantNotFoundException(merchant_id)

        updated = self.merchant_repository.update_merchant_status(db, merchant, active)
        logger.info(
            "Merchant status updated.",
            extra={"merchant_id": merchant_id, "active": active},
        )

        return updated

    def _enforce_merchant_name_uniqueness(self, name: str, db: Session) -> None:
        if self.merchant_repository.get_merchant_by_name(db, name):
            logger.info(
                "Attempt to create a merchant with an existing name.",
                extra={"merchant_name": name},
            )
            raise MerchantNameAlreadyExistsException(name)
