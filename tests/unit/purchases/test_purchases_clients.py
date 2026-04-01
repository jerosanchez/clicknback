from datetime import date
from decimal import Decimal
from typing import Any, Callable
from unittest.mock import AsyncMock, Mock, create_autospec

import pytest

from app.cashback.calculator import CashbackCalculatorABC
from app.cashback.models import CashbackResult, CashbackTransactionStatus
from app.cashback.repositories import CashbackTransactionRepositoryABC
from app.feature_flags.services import FeatureFlagService
from app.merchants.models import Merchant
from app.offers.models import Offer
from app.purchases.clients import (
    CashbackClient,
    CashbackResultDTO,
    FeatureFlagClient,
    MerchantDTO,
    MerchantsClient,
    OfferDTO,
    OffersClient,
    UserDTO,
    UsersClient,
    WalletsClient,
)
from app.purchases.models import Purchase
from app.users.models import User
from app.wallets.repositories import WalletRepositoryABC

# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────


def _stub_scalar_one_or_none(db: AsyncMock, value: Any) -> None:
    """Configure db.execute to return a result whose scalar_one_or_none() == value."""
    mock_result = Mock()
    mock_result.scalar_one_or_none.return_value = value
    db.execute.return_value = mock_result


# ──────────────────────────────────────────────────────────────────────────────
# MerchantsClient
# ──────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_merchants_client_get_by_id_returns_none_on_merchant_not_found() -> None:
    # Arrange
    db = AsyncMock()
    _stub_scalar_one_or_none(db, None)
    client = MerchantsClient()

    # Act
    result = await client.get_merchant_by_id(db, merchant_id="non-existent-id")

    # Assert
    assert result is None


@pytest.mark.asyncio
async def test_merchants_client_get_by_id_returns_dto_on_merchant_found(
    merchant_factory: Callable[..., Merchant],
) -> None:
    # Arrange
    merchant = merchant_factory()
    db = AsyncMock()
    _stub_scalar_one_or_none(db, merchant)
    client = MerchantsClient()

    # Act
    result = await client.get_merchant_by_id(db, merchant_id=str(merchant.id))

    # Assert
    assert isinstance(result, MerchantDTO)
    assert result.id == merchant.id
    assert result.active == merchant.active
    assert result.name == merchant.name


@pytest.mark.asyncio
async def test_merchants_client_get_by_ids_returns_empty_dict_on_empty_list() -> None:
    # Arrange
    db = AsyncMock()
    client = MerchantsClient()

    # Act
    result = await client.get_merchants_by_ids(db, merchant_ids=[])

    # Assert
    assert result == {}
    db.execute.assert_not_called()


@pytest.mark.asyncio
async def test_merchants_client_get_by_ids_returns_dto_dict_on_merchants_found(
    merchant_factory: Callable[..., Merchant],
) -> None:
    # Arrange
    merchant_a = merchant_factory(id="m-id-1", name="Alpha", active=True)
    merchant_b = merchant_factory(id="m-id-2", name="Beta", active=False)
    mock_result = Mock()
    mock_result.scalars.return_value.all.return_value = [merchant_a, merchant_b]
    db = AsyncMock()
    db.execute.return_value = mock_result
    client = MerchantsClient()

    # Act
    result = await client.get_merchants_by_ids(db, merchant_ids=["m-id-1", "m-id-2"])

    # Assert
    assert set(result.keys()) == {"m-id-1", "m-id-2"}
    assert isinstance(result["m-id-1"], MerchantDTO)
    assert result["m-id-1"].name == "Alpha"
    assert result["m-id-2"].active is False


# ──────────────────────────────────────────────────────────────────────────────
# UsersClient
# ──────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_users_client_get_by_id_returns_none_on_user_not_found() -> None:
    # Arrange
    db = AsyncMock()
    _stub_scalar_one_or_none(db, None)
    client = UsersClient()

    # Act
    result = await client.get_user_by_id(db, user_id="non-existent-id")

    # Assert
    assert result is None


@pytest.mark.asyncio
async def test_users_client_get_by_id_returns_dto_on_user_found(
    user_factory: Callable[..., User],
) -> None:
    # Arrange
    user = user_factory()
    db = AsyncMock()
    _stub_scalar_one_or_none(db, user)
    client = UsersClient()

    # Act
    result = await client.get_user_by_id(db, user_id=str(user.id))

    # Assert
    assert isinstance(result, UserDTO)
    assert result.id == user.id
    assert result.active == user.active


# ──────────────────────────────────────────────────────────────────────────────
# OffersClient
# ──────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_offers_client_get_active_offer_returns_none_on_offer_not_found() -> None:
    # Arrange
    db = AsyncMock()
    _stub_scalar_one_or_none(db, None)
    client = OffersClient()

    # Act
    result = await client.get_active_offer_for_merchant(
        db, merchant_id="m-id-1", today=date(2026, 3, 28)
    )

    # Assert
    assert result is None


@pytest.mark.asyncio
async def test_offers_client_get_active_offer_returns_dto_on_offer_found(
    offer_factory: Callable[..., Offer],
) -> None:
    # Arrange
    offer = offer_factory()
    db = AsyncMock()
    _stub_scalar_one_or_none(db, offer)
    client = OffersClient()

    # Act
    result = await client.get_active_offer_for_merchant(
        db, merchant_id=str(offer.merchant_id), today=date(2026, 3, 28)
    )

    # Assert
    assert isinstance(result, OfferDTO)
    assert result.id == offer.id
    assert result.merchant_id == offer.merchant_id
    assert result.active == offer.active
    assert result.start_date == offer.start_date
    assert result.end_date == offer.end_date
    assert result.percentage == offer.percentage
    assert result.fixed_amount == offer.fixed_amount


# ──────────────────────────────────────────────────────────────────────────────
# CashbackClient
# ──────────────────────────────────────────────────────────────────────────────


@pytest.fixture
def calculator_mock() -> Mock:
    return create_autospec(CashbackCalculatorABC)


@pytest.fixture
def cashback_repo_mock() -> Mock:
    return create_autospec(CashbackTransactionRepositoryABC)


@pytest.fixture
def cashback_client(calculator_mock: Mock, cashback_repo_mock: Mock) -> CashbackClient:
    client = CashbackClient(calculator=calculator_mock)
    client._repository = cashback_repo_mock  # pyright: ignore[reportPrivateUsage]
    return client


def test_cashback_client_calculate_returns_dto_with_correct_fields(
    cashback_client: CashbackClient,
    calculator_mock: Mock,
) -> None:
    # Arrange
    offer_id = "f0e1d2c3-b4a5-4678-9012-3456789abcde"
    purchase_amount = Decimal("100.00")
    cashback_amount = Decimal("10.00")
    calculator_mock.calculate.return_value = CashbackResult(
        offer_id=offer_id,
        cashback_amount=cashback_amount,
        percentage_applied=10.0,
        fixed_amount_applied=None,
    )

    # Act
    result = cashback_client.calculate(
        offer_id=offer_id,
        percentage=10.0,
        fixed_amount=None,
        purchase_amount=purchase_amount,
    )

    # Assert
    assert isinstance(result, CashbackResultDTO)
    assert result.offer_id == offer_id
    assert result.cashback_amount == cashback_amount


@pytest.mark.asyncio
async def test_cashback_client_create_delegates_to_repository(
    cashback_client: CashbackClient,
    cashback_repo_mock: Mock,
) -> None:
    # Arrange
    db = AsyncMock()
    purchase_id = "aa000001-0000-0000-0000-000000000001"
    user_id = "b7e2c1a2-4f3a-4e2b-9c1a-8d2e3f4b5c6d"
    amount = Decimal("5.00")

    # Act
    await cashback_client.create(
        db, purchase_id=purchase_id, user_id=user_id, amount=amount
    )

    # Assert
    cashback_repo_mock.create.assert_called_once_with(db, purchase_id, user_id, amount)


@pytest.mark.asyncio
async def test_cashback_client_confirm_delegates_to_repository_with_available_status(
    cashback_client: CashbackClient,
    cashback_repo_mock: Mock,
) -> None:
    # Arrange
    db = AsyncMock()
    purchase_id = "aa000001-0000-0000-0000-000000000001"

    # Act
    await cashback_client.confirm(db, purchase_id=purchase_id)

    # Assert
    cashback_repo_mock.update_status.assert_called_once_with(
        db, purchase_id, CashbackTransactionStatus.AVAILABLE.value
    )


@pytest.mark.asyncio
async def test_cashback_client_reverse_delegates_to_repository_with_reversed_status(
    cashback_client: CashbackClient,
    cashback_repo_mock: Mock,
) -> None:
    # Arrange
    db = AsyncMock()
    purchase_id = "aa000001-0000-0000-0000-000000000001"

    # Act
    await cashback_client.reverse(db, purchase_id=purchase_id)

    # Assert
    cashback_repo_mock.update_status.assert_called_once_with(
        db, purchase_id, CashbackTransactionStatus.REVERSED.value
    )


# ──────────────────────────────────────────────────────────────────────────────
# WalletsClient
# ──────────────────────────────────────────────────────────────────────────────


@pytest.fixture
def wallet_repo_mock() -> Mock:
    return create_autospec(WalletRepositoryABC)


@pytest.fixture
def wallets_client(wallet_repo_mock: Mock) -> WalletsClient:
    client = WalletsClient()
    client._repository = wallet_repo_mock  # pyright: ignore[reportPrivateUsage]
    return client


@pytest.mark.asyncio
async def test_wallets_client_credit_pending_delegates_to_repository(
    wallets_client: WalletsClient,
    wallet_repo_mock: Mock,
) -> None:
    # Arrange
    db = AsyncMock()
    user_id = "b7e2c1a2-4f3a-4e2b-9c1a-8d2e3f4b5c6d"
    amount = Decimal("10.00")

    # Act
    await wallets_client.credit_pending(db, user_id=user_id, amount=amount)

    # Assert
    wallet_repo_mock.credit_pending.assert_called_once_with(db, user_id, amount)


@pytest.mark.asyncio
async def test_wallets_client_confirm_pending_delegates_to_repository(
    wallets_client: WalletsClient,
    wallet_repo_mock: Mock,
) -> None:
    # Arrange
    db = AsyncMock()
    user_id = "b7e2c1a2-4f3a-4e2b-9c1a-8d2e3f4b5c6d"
    amount = Decimal("10.00")

    # Act
    await wallets_client.confirm_pending(db, user_id=user_id, amount=amount)

    # Assert
    wallet_repo_mock.confirm_pending.assert_called_once_with(db, user_id, amount)


@pytest.mark.asyncio
async def test_wallets_client_reverse_pending_delegates_to_repository(
    wallets_client: WalletsClient,
    wallet_repo_mock: Mock,
) -> None:
    # Arrange
    db = AsyncMock()
    user_id = "b7e2c1a2-4f3a-4e2b-9c1a-8d2e3f4b5c6d"
    amount = Decimal("10.00")

    # Act
    await wallets_client.reverse_pending(db, user_id=user_id, amount=amount)

    # Assert
    wallet_repo_mock.reverse_pending.assert_called_once_with(db, user_id, amount)


@pytest.mark.asyncio
async def test_wallets_client_reverse_available_delegates_to_repository(
    wallets_client: WalletsClient,
    wallet_repo_mock: Mock,
) -> None:
    # Arrange
    db = AsyncMock()
    user_id = "b7e2c1a2-4f3a-4e2b-9c1a-8d2e3f4b5c6d"
    amount = Decimal("10.00")

    # Act
    await wallets_client.reverse_available(db, user_id=user_id, amount=amount)

    # Assert
    wallet_repo_mock.reverse_available.assert_called_once_with(db, user_id, amount)


# ──────────────────────────────────────────────────────────────────────────────
# FeatureFlagClient — purchase auto-confirm eligibility filtering
# ──────────────────────────────────────────────────────────────────────────────


def _make_purchase(**kwargs: Any) -> Purchase:
    """Build a minimal Purchase ORM instance for tests."""
    defaults = {
        "id": "purchase-001",
        "external_id": "ext-001",
        "user_id": "user-123",
        "merchant_id": "merchant-456",
        "offer_id": None,
        "amount": Decimal("100.00"),
        "cashback_amount": Decimal("0"),
        "currency": "USD",
        "status": "pending",
        "created_at": kwargs.pop("created_at", None),
    }
    defaults.update(kwargs)
    return Purchase(**defaults)


@pytest.fixture
def feature_flag_service_mock() -> Mock:
    return create_autospec(FeatureFlagService)


@pytest.fixture
def feature_flag_client(feature_flag_service_mock: Mock) -> FeatureFlagClient:
    return FeatureFlagClient(feature_flag_service=feature_flag_service_mock)


@pytest.mark.asyncio
async def test_feature_flag_client_filter_eligible_purchases_returns_empty_for_empty_list(
    feature_flag_client: FeatureFlagClient,
    feature_flag_service_mock: Mock,
) -> None:
    # Arrange
    db = AsyncMock()

    # Act
    eligible, ineligible = await feature_flag_client.filter_eligible_purchases(db, [])

    # Assert
    assert eligible == []
    assert ineligible == 0
    feature_flag_service_mock.is_enabled.assert_not_called()


@pytest.mark.asyncio
async def test_feature_flag_client_filter_eligible_purchases_scoped_overrides_global_disabled(
    feature_flag_client: FeatureFlagClient,
    feature_flag_service_mock: Mock,
) -> None:
    # Arrange
    db = AsyncMock()
    user_id_1 = "user-1"
    merchant_id_1 = "merchant-1"
    user_id_2 = "user-2"
    merchant_id_2 = "merchant-2"
    purchases = [
        _make_purchase(id="p1", user_id=user_id_1, merchant_id=merchant_id_1),
        _make_purchase(id="p2", user_id=user_id_2, merchant_id=merchant_id_2),
    ]
    # Global flag disabled, but scoped flags can override it
    scope_results = {
        ("user", user_id_1): True,  # Scoped enabled - overrides global
        ("merchant", merchant_id_1): True,
        ("user", user_id_2): False,  # Scoped disabled
        ("merchant", merchant_id_2): True,
    }
    feature_flag_service_mock.evaluate_scopes.return_value = scope_results

    # Act
    eligible, ineligible = await feature_flag_client.filter_eligible_purchases(
        db, purchases
    )

    # Assert
    # p1 is eligible because both scopes are enabled (scoped overrides global)
    # p2 is ineligible because user scope is disabled
    assert len(eligible) == 1
    assert eligible[0].id == "p1"
    assert ineligible == 1
    # Should call evaluate_scopes to check all scopes (no early global check)
    feature_flag_service_mock.evaluate_scopes.assert_called_once()


@pytest.mark.asyncio
async def test_feature_flag_client_filter_eligible_purchases_all_eligible_when_all_scopes_enabled(
    feature_flag_client: FeatureFlagClient,
    feature_flag_service_mock: Mock,
) -> None:
    # Arrange
    db = AsyncMock()
    user_id_1 = str(id("user-1"))
    merchant_id_1 = str(id("merchant-1"))
    user_id_2 = str(id("user-2"))
    merchant_id_2 = str(id("merchant-2"))
    purchases = [
        _make_purchase(id="p1", user_id=user_id_1, merchant_id=merchant_id_1),
        _make_purchase(id="p2", user_id=user_id_2, merchant_id=merchant_id_2),
    ]
    # All scopes enabled
    scope_results = {
        ("user", user_id_1): True,
        ("merchant", merchant_id_1): True,
        ("user", user_id_2): True,
        ("merchant", merchant_id_2): True,
    }
    feature_flag_service_mock.evaluate_scopes.return_value = scope_results

    # Act
    eligible, ineligible = await feature_flag_client.filter_eligible_purchases(
        db, purchases
    )

    # Assert
    assert len(eligible) == 2
    assert ineligible == 0
    feature_flag_service_mock.evaluate_scopes.assert_called_once()


@pytest.mark.asyncio
async def test_feature_flag_client_filter_eligible_purchases_mixed_eligibility(
    feature_flag_client: FeatureFlagClient,
    feature_flag_service_mock: Mock,
) -> None:
    # Arrange
    db = AsyncMock()
    user_id_1 = "user-1"
    merchant_id_1 = "merchant-1"
    user_id_2 = "user-2"
    merchant_id_2 = "merchant-2"
    purchases = [
        _make_purchase(id="p1", user_id=user_id_1, merchant_id=merchant_id_1),
        _make_purchase(id="p2", user_id=user_id_2, merchant_id=merchant_id_2),
    ]
    # Mixed eligibility: p1 eligible, p2 ineligible (user disabled)
    scope_results = {
        ("user", user_id_1): True,
        ("merchant", merchant_id_1): True,
        ("user", user_id_2): False,  # User disabled
        ("merchant", merchant_id_2): True,
    }
    feature_flag_service_mock.evaluate_scopes.return_value = scope_results

    # Act
    eligible, ineligible = await feature_flag_client.filter_eligible_purchases(
        db, purchases
    )

    # Assert
    assert len(eligible) == 1
    assert eligible[0].id == "p1"
    assert ineligible == 1


@pytest.mark.asyncio
async def test_feature_flag_client_filter_eligible_purchases_excludes_merchant_disabled(
    feature_flag_client: FeatureFlagClient,
    feature_flag_service_mock: Mock,
) -> None:
    # Arrange
    db = AsyncMock()
    user_id_1 = "user-1"
    merchant_id_1 = "merchant-1"
    purchases = [
        _make_purchase(id="p1", user_id=user_id_1, merchant_id=merchant_id_1),
    ]
    # Merchant disabled, user enabled
    scope_results = {
        ("user", user_id_1): True,
        ("merchant", merchant_id_1): False,  # Merchant disabled
    }
    feature_flag_service_mock.evaluate_scopes.return_value = scope_results

    # Act
    eligible, ineligible = await feature_flag_client.filter_eligible_purchases(
        db, purchases
    )

    # Assert
    assert len(eligible) == 0
    assert ineligible == 1


@pytest.mark.asyncio
async def test_feature_flag_client_filter_eligible_purchases_requires_both_scopes_enabled(
    feature_flag_client: FeatureFlagClient,
    feature_flag_service_mock: Mock,
) -> None:
    # Arrange
    db = AsyncMock()
    user_id = "user-1"
    merchant_id = "merchant-1"
    purchases = [
        _make_purchase(id="p1", user_id=user_id, merchant_id=merchant_id),
    ]
    # Both disabled
    scope_results = {
        ("user", user_id): False,
        ("merchant", merchant_id): False,
    }
    feature_flag_service_mock.evaluate_scopes.return_value = scope_results

    # Act
    eligible, ineligible = await feature_flag_client.filter_eligible_purchases(
        db, purchases
    )

    # Assert
    assert len(eligible) == 0
    assert ineligible == 1


@pytest.mark.asyncio
async def test_feature_flag_client_filter_eligible_purchases_collects_unique_scopes(
    feature_flag_client: FeatureFlagClient,
    feature_flag_service_mock: Mock,
) -> None:
    # Arrange
    db = AsyncMock()
    # Multiple purchases from same user and merchant
    user_id = "user-1"
    merchant_id = "merchant-1"
    purchases = [
        _make_purchase(id="p1", user_id=user_id, merchant_id=merchant_id),
        _make_purchase(id="p2", user_id=user_id, merchant_id=merchant_id),
        _make_purchase(id="p3", user_id=user_id, merchant_id=merchant_id),
    ]
    # Both scopes enabled
    scope_results = {
        ("user", user_id): True,
        ("merchant", merchant_id): True,
    }
    feature_flag_service_mock.evaluate_scopes.return_value = scope_results

    # Act
    eligible, ineligible = await feature_flag_client.filter_eligible_purchases(
        db, purchases
    )

    # Assert
    # Should call evaluate_scopes with unique scopes only (not 6 calls)
    assert len(eligible) == 3
    assert ineligible == 0
    # Verify it called with set converted to list (order doesn't matter)
    call_args = feature_flag_service_mock.evaluate_scopes.call_args
    scopes_called = call_args[0][2]  # Third positional arg is scopes
    assert len(scopes_called) == 2  # Only 2 unique scopes
    assert ("user", user_id) in scopes_called
    assert ("merchant", merchant_id) in scopes_called
