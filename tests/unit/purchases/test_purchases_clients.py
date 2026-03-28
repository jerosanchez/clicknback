from datetime import date
from decimal import Decimal
from typing import Any, Callable
from unittest.mock import AsyncMock, Mock, create_autospec

import pytest

from app.cashback.calculator import CashbackCalculatorABC
from app.cashback.models import CashbackResult, CashbackTransactionStatus
from app.cashback.repositories import CashbackTransactionRepositoryABC
from app.merchants.models import Merchant
from app.offers.models import Offer
from app.purchases.clients import (
    CashbackClient,
    CashbackResultDTO,
    MerchantDTO,
    MerchantsClient,
    OfferDTO,
    OffersClient,
    UserDTO,
    UsersClient,
    WalletsClient,
)
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
    client._repository = cashback_repo_mock
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
    client._repository = wallet_repo_mock
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
