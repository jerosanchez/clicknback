from datetime import datetime, timezone

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.broker import broker
from app.core.config import settings
from app.core.database import AsyncSessionLocal, get_async_db
from app.core.unit_of_work import SQLAlchemyUnitOfWork, UnitOfWorkABC
from app.feature_flags.composition import get_feature_flag_service
from app.purchases.clients import (
    CashbackClient,
    FeatureFlagClient,
    MerchantsClient,
    OffersClient,
    UsersClient,
    WalletsClient,
)
from app.purchases.jobs.verify_purchases import (
    SimulatedPurchaseVerifier,
    make_verify_purchases_task,
)
from app.purchases.policies import (
    enforce_currency_eur,
    enforce_merchant_active,
    enforce_offer_available,
    enforce_purchase_ownership,
    enforce_purchase_pending,
    enforce_purchase_reversible,
    enforce_purchase_view_ownership,
    enforce_user_active,
)
from app.purchases.repositories import PurchaseRepository
from app.purchases.services import PurchaseService


def get_purchase_repository() -> PurchaseRepository:
    return PurchaseRepository()


def get_wallets_client() -> WalletsClient:
    return WalletsClient()


def get_cashback_client() -> CashbackClient:
    return CashbackClient()


def get_feature_flag_client() -> FeatureFlagClient:
    return FeatureFlagClient(feature_flag_service=get_feature_flag_service())


def get_unit_of_work(db: AsyncSession = Depends(get_async_db)) -> UnitOfWorkABC:
    return SQLAlchemyUnitOfWork(db)


def get_purchase_service() -> PurchaseService:
    return PurchaseService(
        repository=get_purchase_repository(),
        cashback_client=get_cashback_client(),
        wallets_client=get_wallets_client(),
        users_client=UsersClient(),
        merchants_client=MerchantsClient(),
        offers_client=OffersClient(),
        enforce_purchase_ownership=enforce_purchase_ownership,
        enforce_user_active=enforce_user_active,
        enforce_merchant_active=enforce_merchant_active,
        enforce_offer_available=enforce_offer_available,
        enforce_currency_supported=enforce_currency_eur,
        enforce_purchase_view_ownership=enforce_purchase_view_ownership,
        enforce_purchase_reversible=enforce_purchase_reversible,
        enforce_purchase_pending=enforce_purchase_pending,
        broker=broker,
    )


def get_verify_purchases_task():
    return make_verify_purchases_task(
        repository=PurchaseRepository(),
        wallets_client=get_wallets_client(),
        cashback_client=get_cashback_client(),
        broker=broker,
        db_session_factory=AsyncSessionLocal,
        feature_flag_client=get_feature_flag_client(),
        verifier=SimulatedPurchaseVerifier(
            rejection_merchant_id=settings.rejection_merchant_id,
        ),
        max_attempts=settings.purchase_max_verification_attempts,
        retry_interval_seconds=settings.purchase_confirmation_interval_seconds,
        datetime_provider=lambda: datetime.now(timezone.utc),
    )
