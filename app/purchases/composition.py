from datetime import datetime, timezone

from app.core.audit.composition import get_audit_trail
from app.core.broker import broker
from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.purchases.clients import MerchantsClient, OffersClient, UsersClient
from app.purchases.jobs.verify_purchases import (
    SimulatedPurchaseVerifier,
    make_verify_purchases_task,
)
from app.purchases.policies import (
    enforce_currency_eur,
    enforce_merchant_active,
    enforce_offer_available,
    enforce_purchase_ownership,
    enforce_purchase_view_ownership,
    enforce_user_active,
)
from app.purchases.repositories import PurchaseRepository
from app.purchases.services import PurchaseService


def get_purchase_repository() -> PurchaseRepository:
    return PurchaseRepository()


def get_purchase_service() -> PurchaseService:
    return PurchaseService(
        repository=get_purchase_repository(),
        users_client=UsersClient(),
        merchants_client=MerchantsClient(),
        offers_client=OffersClient(),
        enforce_purchase_ownership=enforce_purchase_ownership,
        enforce_user_active=enforce_user_active,
        enforce_merchant_active=enforce_merchant_active,
        enforce_offer_available=enforce_offer_available,
        enforce_currency_supported=enforce_currency_eur,
        enforce_purchase_view_ownership=enforce_purchase_view_ownership,
    )


def get_verify_purchases_task():
    return make_verify_purchases_task(
        repository=PurchaseRepository(),
        audit_trail=get_audit_trail(),
        broker=broker,
        db_session_factory=AsyncSessionLocal,
        verifier=SimulatedPurchaseVerifier(
            rejection_merchant_id=settings.rejection_merchant_id,
        ),
        max_attempts=settings.purchase_max_verification_attempts,
        retry_interval_seconds=settings.purchase_confirmation_interval_seconds,
        datetime_provider=lambda: datetime.now(timezone.utc),
    )
