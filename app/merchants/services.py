from typing import Any, Callable

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import logger
from app.core.unit_of_work import UnitOfWorkABC
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

    async def create_merchant(
        self, merchant_data: dict[str, Any], uow: UnitOfWorkABC
    ) -> Merchant:
        default_cashback_percentage = merchant_data["default_cashback_percentage"]
        name = merchant_data["name"]
        active = merchant_data["active"]

        self.enforce_cashback_percentage_validity(default_cashback_percentage)

        await self._enforce_merchant_name_uniqueness(name, uow.session)

        new_merchant = Merchant(
            name=name,
            default_cashback_percentage=default_cashback_percentage,
            active=active,
        )

        result = await self.merchant_repository.add_merchant(uow.session, new_merchant)
        await uow.commit()
        return result

    async def list_merchants(
        self,
        offset: int,
        limit: int,
        active: bool | None,
        db: AsyncSession,
    ) -> tuple[list[Merchant], int]:
        return await self.merchant_repository.list_merchants(db, offset, limit, active)

    async def set_merchant_status(
        self, merchant_id: str, active: bool, uow: UnitOfWorkABC
    ) -> Merchant:
        merchant = await self.merchant_repository.get_merchant_by_id(
            uow.session, merchant_id
        )
        if merchant is None:
            logger.debug(
                "Merchant not found for status update.",
                extra={"merchant_id": merchant_id},
            )
            raise MerchantNotFoundException(merchant_id)

        updated = await self.merchant_repository.update_merchant_status(
            uow.session, merchant, active
        )
        await uow.commit()
        logger.info(
            "Merchant status updated.",
            extra={"merchant_id": merchant_id, "active": active},
        )
        return updated

    async def _enforce_merchant_name_uniqueness(
        self, name: str, db: AsyncSession
    ) -> None:
        if await self.merchant_repository.get_merchant_by_name(db, name):
            logger.info(
                "Attempt to create a merchant with an existing name.",
                extra={"merchant_name": name},
            )
            raise MerchantNameAlreadyExistsException(name)
