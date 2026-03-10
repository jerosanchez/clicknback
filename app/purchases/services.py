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
from app.purchases.exceptions import (
    DuplicatePurchaseException,
    InvalidPurchaseStatusException,
    PurchaseNotFoundException,
)
from app.purchases.models import Purchase
from app.purchases.repositories import PurchaseRepositoryABC
from app.purchases.schemas import PurchaseStatus


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
        enforce_purchase_view_ownership: Callable[[str, str, str], None],
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
        self.enforce_purchase_view_ownership = enforce_purchase_view_ownership

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

    async def list_purchases(
        self,
        db: AsyncSession,
        *,
        status: str | None = None,
        user_id: str | None = None,
        merchant_id: str | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
        page: int = 1,
        page_size: int = 10,
    ) -> tuple[list[Purchase], int]:
        if status is not None:
            try:
                PurchaseStatus(status)
            except ValueError:
                raise InvalidPurchaseStatusException(status)
        return await self.repository.list_purchases(
            db,
            status=status,
            user_id=user_id,
            merchant_id=merchant_id,
            start_date=start_date,
            end_date=end_date,
            page=page,
            page_size=page_size,
        )

    async def get_purchase_details(
        self, purchase_id: str, current_user_id: str, db: AsyncSession
    ) -> tuple[Purchase, str]:
        purchase = await self.repository.get_by_id(db, purchase_id)
        if purchase is None:
            raise PurchaseNotFoundException(purchase_id)

        self.enforce_purchase_view_ownership(
            current_user_id, purchase.user_id, purchase_id
        )

        merchant = await self.merchants_client.get_merchant_by_id(
            db, purchase.merchant_id
        )

        # Merchant should always exist for a valid purchase; fall back gracefully if not
        if merchant is None:
            logger.warning(
                "Merchant not found for purchase.",
                extra={"purchase_id": purchase.id, "merchant_id": purchase.merchant_id},
            )
            merchant_name = "Unknown"
        else:
            merchant_name = merchant.name

        return purchase, merchant_name
