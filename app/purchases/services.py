from datetime import date
from typing import Any, Callable

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import logger
from app.purchases.clients import (
    MerchantDTO,
    MerchantsClientABC,
    OfferDTO,
    OffersClientABC,
    UserDTO,
    UsersClientABC,
)
from app.purchases.exceptions import DuplicatePurchaseException
from app.purchases.models import Purchase
from app.purchases.repositories import PurchaseRepositoryABC


class PurchaseService:
    def __init__(
        self,
        repository: PurchaseRepositoryABC,
        users_client: UsersClientABC,
        merchants_client: MerchantsClientABC,
        offers_client: OffersClientABC,
        enforce_purchase_ownership: Callable[[str, str], None],
        enforce_user_active: Callable[[UserDTO | None, str], None],
        enforce_merchant_active: Callable[[MerchantDTO | None, str], None],
        enforce_offer_available: Callable[[OfferDTO | None, str], None],
        enforce_currency_supported: Callable[[str], None],
    ):
        self.repository = repository
        self.users_client = users_client
        self.merchants_client = merchants_client
        self.offers_client = offers_client
        self.enforce_purchase_ownership = enforce_purchase_ownership
        self.enforce_user_active = enforce_user_active
        self.enforce_merchant_active = enforce_merchant_active
        self.enforce_offer_available = enforce_offer_available
        self.enforce_currency_supported = enforce_currency_supported

    async def ingest_purchase(
        self, data: dict[str, Any], current_user_id: str, db: AsyncSession
    ) -> Purchase:
        external_id: str = data["external_id"]
        user_id: str = str(data["user_id"])
        merchant_id: str = str(data["merchant_id"])
        amount = data["amount"]
        currency: str = data["currency"]

        self.enforce_purchase_ownership(current_user_id, user_id)

        existing = await self.repository.get_by_external_id(db, external_id)
        if existing is not None:
            logger.debug(
                "Duplicate purchase detected.",
                extra={"external_id": external_id},
            )
            raise DuplicatePurchaseException(
                external_id, existing.created_at, existing.amount
            )

        self.enforce_currency_supported(currency)

        user = await self.users_client.get_user_by_id(db, user_id)
        self.enforce_user_active(user, user_id)

        merchant = await self.merchants_client.get_merchant_by_id(db, merchant_id)
        self.enforce_merchant_active(merchant, merchant_id)

        today = date.today()
        offer = await self.offers_client.get_active_offer_for_merchant(
            db, merchant_id, today
        )
        self.enforce_offer_available(offer, merchant_id)

        new_purchase = Purchase(
            external_id=external_id,
            user_id=user_id,
            merchant_id=merchant_id,
            offer_id=offer.id,  # type: ignore[union-attr]
            amount=amount,
            currency=currency,
        )

        result = await self.repository.add_purchase(db, new_purchase)
        logger.info(
            "Purchase ingested successfully.",
            extra={"purchase_id": result.id, "external_id": external_id},
        )
        return result
