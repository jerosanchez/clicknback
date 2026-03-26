from datetime import date
from decimal import Decimal
from typing import Any, Callable

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.broker import MessageBrokerABC
from app.core.events.purchase_events import PurchaseReversed
from app.core.logging import logger
from app.core.unit_of_work import UnitOfWorkABC
from app.purchases.clients import (
    CashbackClientABC,
    MerchantDTO,
    MerchantsClientABC,
    OfferDTO,
    OffersClientABC,
    UserDTO,
    UsersClientABC,
    WalletsClientABC,
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
        cashback_client: CashbackClientABC,
        wallets_client: WalletsClientABC,
        users_client: UsersClientABC,
        merchants_client: MerchantsClientABC,
        offers_client: OffersClientABC,
        enforce_purchase_ownership: Callable[[str, str], None],
        enforce_user_active: Callable[[UserDTO | None, str], None],
        enforce_merchant_active: Callable[[MerchantDTO | None, str], None],
        enforce_offer_available: Callable[[OfferDTO | None, str], None],
        enforce_currency_supported: Callable[[str], None],
        enforce_purchase_view_ownership: Callable[[str, str, str], None],
        enforce_purchase_reversible: Callable[[str, str], None],
        broker: MessageBrokerABC,
    ):
        self.repository = repository
        self.cashback_client = cashback_client
        self.wallets_client = wallets_client
        self.users_client = users_client
        self.merchants_client = merchants_client
        self.offers_client = offers_client
        self.enforce_purchase_ownership = enforce_purchase_ownership
        self.enforce_user_active = enforce_user_active
        self.enforce_merchant_active = enforce_merchant_active
        self.enforce_offer_available = enforce_offer_available
        self.enforce_currency_supported = enforce_currency_supported
        self.enforce_purchase_view_ownership = enforce_purchase_view_ownership
        self.enforce_purchase_reversible = enforce_purchase_reversible
        self.broker = broker

    async def ingest_purchase(
        self, data: dict[str, Any], current_user_id: str, uow: UnitOfWorkABC
    ) -> Purchase:
        external_id: str = data["external_id"]
        user_id: str = str(data["user_id"])
        merchant_id: str = str(data["merchant_id"])
        amount = data["amount"]
        currency: str = data["currency"]

        self.enforce_purchase_ownership(current_user_id, user_id)

        db = uow.session

        # Get existing purchase
        existing = await self.repository.get_by_external_id(db, external_id)
        if existing is not None:
            logger.debug(
                "Duplicate purchase detected.",
                extra={"external_id": external_id},
            )
            raise DuplicatePurchaseException(
                external_id, existing.created_at, existing.amount
            )

        # Ensure currency is supported
        self.enforce_currency_supported(currency)

        # Get user, merchant and offer details
        user = await self.users_client.get_user_by_id(db, user_id)
        self.enforce_user_active(user, user_id)

        merchant = await self.merchants_client.get_merchant_by_id(db, merchant_id)
        self.enforce_merchant_active(merchant, merchant_id)

        today = date.today()
        offer = await self.offers_client.get_active_offer_for_merchant(
            db, merchant_id, today
        )
        self.enforce_offer_available(offer, merchant_id)

        # Calculate cashback amount
        cashback_result = self.cashback_client.calculate(
            offer_id=offer.id,  # type: ignore[union-attr]
            percentage=offer.percentage,  # type: ignore[union-attr]
            fixed_amount=offer.fixed_amount,  # type: ignore[union-attr]
            purchase_amount=amount,
        )
        cashback_amount = cashback_result.cashback_amount

        # Create new purchase record
        new_purchase = Purchase(
            external_id=external_id,
            user_id=user_id,
            merchant_id=merchant_id,
            offer_id=offer.id,  # type: ignore[union-attr]
            amount=amount,
            cashback_amount=cashback_amount,
            currency=currency,
        )

        # Flush purchase, cashback transaction, and wallet credit
        result = await self.repository.add_purchase(db, new_purchase)
        await self.cashback_client.create(db, result.id, user_id, cashback_amount)
        await self.wallets_client.credit_pending(db, user_id, cashback_amount)

        # Commit all changes together to ensure atomicity
        await uow.commit()

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
            except ValueError as exc:
                raise InvalidPurchaseStatusException(status) from exc
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

    async def list_user_purchases(
        self,
        db: AsyncSession,
        current_user_id: str,
        *,
        status: str | None = None,
        page: int = 1,
        page_size: int = 10,
    ) -> tuple[list[tuple[Purchase, str]], int]:
        if status is not None:
            try:
                PurchaseStatus(status)
            except ValueError as exc:
                raise InvalidPurchaseStatusException(status) from exc

        purchases, total = await self.repository.list_purchases(
            db,
            user_id=current_user_id,
            status=status,
            page=page,
            page_size=page_size,
        )

        # Batch-load all merchant names in a single query to avoid N+1 (ADR-019)
        unique_merchant_ids = list({p.merchant_id for p in purchases})
        merchants_map = await self.merchants_client.get_merchants_by_ids(
            db, unique_merchant_ids
        )

        enriched: list[tuple[Purchase, str]] = [
            (
                p,
                (
                    merchants_map[p.merchant_id].name
                    if p.merchant_id in merchants_map
                    else "Unknown"
                ),
            )
            for p in purchases
        ]
        return enriched, total

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

    async def reverse_purchase(
        self, purchase_id: str, admin_id: str, uow: UnitOfWorkABC
    ) -> Purchase:
        db = uow.session

        purchase = await self.repository.get_by_id(db, purchase_id)
        if purchase is None:
            raise PurchaseNotFoundException(purchase_id)

        self.enforce_purchase_reversible(purchase_id, purchase.status)

        original_cashback_amount: Decimal = purchase.cashback_amount
        prior_status: str = purchase.status

        # Reverse cashback transaction first, then adjust wallet
        await self.cashback_client.reverse(db, purchase_id)

        if prior_status == "pending":
            await self.wallets_client.reverse_pending(
                db, purchase.user_id, original_cashback_amount
            )
        else:
            # confirmed status — deduct from available_balance
            await self.wallets_client.reverse_available(
                db, purchase.user_id, original_cashback_amount
            )

        reversed_purchase = await self.repository.reverse_purchase(db, purchase_id)

        await uow.commit()

        await self.broker.publish(
            PurchaseReversed(
                purchase_id=purchase_id,
                user_id=purchase.user_id,
                admin_id=admin_id,
                merchant_id=purchase.merchant_id,
                amount=purchase.amount,
                currency=purchase.currency,
                prior_status=prior_status,
            )
        )

        logger.info(
            "Purchase reversed successfully.",
            extra={"purchase_id": purchase_id, "admin_id": admin_id},
        )

        return reversed_purchase  # type: ignore[return-value]
