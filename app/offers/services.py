from datetime import date
from typing import Any, Callable
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.logging import logger
from app.merchants.exceptions import MerchantNotFoundException
from app.merchants.repository import MerchantRepositoryABC
from app.offers.models import Offer
from app.offers.repositories import OfferRepositoryABC
from app.offers.schemas import CashbackTypeEnum


class OfferService:
    def __init__(
        self,
        enforce_cashback_value_validity: Callable[[CashbackTypeEnum, float], None],
        enforce_date_range_validity: Callable[[date, date], None],
        enforce_monthly_cap_validity: Callable[[float], None],
        enforce_merchant_is_active: Callable[[str, bool], None],
        enforce_no_active_offer_exists: Callable[[str, bool], None],
        offer_repository: OfferRepositoryABC,
        merchant_repository: MerchantRepositoryABC,
    ):
        self.enforce_cashback_value_validity = enforce_cashback_value_validity
        self.enforce_date_range_validity = enforce_date_range_validity
        self.enforce_monthly_cap_validity = enforce_monthly_cap_validity
        self.enforce_merchant_is_active = enforce_merchant_is_active
        self.enforce_no_active_offer_exists = enforce_no_active_offer_exists
        self.offer_repository = offer_repository
        self.merchant_repository = merchant_repository

    def create_offer(self, data: dict[str, Any], db: Session) -> Offer:
        # Fail fast: validate offer configuration before any DB look-up.
        self.enforce_cashback_value_validity(
            data["cashback_type"], data["cashback_value"]
        )
        self.enforce_date_range_validity(data["start_date"], data["end_date"])
        self.enforce_monthly_cap_validity(data["monthly_cap"])

        # Validate merchant exists.
        merchant_id = str(data["merchant_id"])
        merchant = self.merchant_repository.get_merchant_by_id(db, merchant_id)
        if merchant is None:
            logger.debug(
                "Offer creation failed: merchant not found.",
                extra={"merchant_id": merchant_id},
            )
            raise MerchantNotFoundException(merchant_id)

        # Validate merchant is active.
        self.enforce_merchant_is_active(merchant_id, merchant.active)

        # Enforce one-active-offer-per-merchant invariant.
        has_active = self.offer_repository.has_active_offer_for_merchant(
            db, merchant_id
        )
        self.enforce_no_active_offer_exists(merchant_id, has_active)

        new_offer = self._map_to_domain_offer(data)

        offer = self.offer_repository.add_offer(db, new_offer)
        logger.info(
            "Offer created successfully.",
            extra={"offer_id": offer.id, "merchant_id": offer.merchant_id},
        )
        return offer

    def _map_to_domain_offer(self, data: dict[str, Any]) -> Offer:
        if data["cashback_type"] == CashbackTypeEnum.percent:
            percentage = data["cashback_value"]
            fixed_amount = None
        else:
            percentage = 0.0
            fixed_amount = data["cashback_value"]

        return Offer(
            merchant_id=str(data["merchant_id"]),
            percentage=percentage,
            fixed_amount=fixed_amount,
            start_date=data["start_date"],
            end_date=data["end_date"],
            monthly_cap_per_user=data["monthly_cap"],
        )

    def list_offers(
        self,
        page: int,
        page_size: int,
        active: bool | None,
        merchant_id: UUID | None,
        date_from: date | None,
        date_to: date | None,
        db: Session,
    ) -> tuple[list[Offer], int]:
        return self.offer_repository.list_offers(
            db,
            page,
            page_size,
            active=active,
            merchant_id=str(merchant_id) if merchant_id is not None else None,
            date_from=date_from,
            date_to=date_to,
        )

    def list_active_offers(
        self,
        page: int,
        page_size: int,
        today: date,
        db: Session,
    ) -> tuple[list[tuple[Offer, str]], int]:
        return self.offer_repository.list_active_offers(db, page, page_size, today)
