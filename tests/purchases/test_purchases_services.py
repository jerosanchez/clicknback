from datetime import date, datetime
from decimal import Decimal
from typing import Any, Callable
from unittest.mock import AsyncMock, Mock, create_autospec

import pytest

from app.purchases.clients import MerchantsClientABC, OffersClientABC, UsersClientABC
from app.purchases.exceptions import (
    DuplicatePurchaseException,
    InvalidPurchaseStatusException,
    MerchantInactiveException,
    MerchantNotFoundException,
    OfferNotAvailableException,
    PurchaseOwnershipViolationException,
    UnsupportedCurrencyException,
    UserInactiveException,
    UserNotFoundException,
)
from app.purchases.models import Purchase
from app.purchases.repositories import PurchaseRepositoryABC
from app.purchases.services import PurchaseService


@pytest.fixture
def purchase_repository() -> Mock:
    return create_autospec(PurchaseRepositoryABC)


@pytest.fixture
def users_client() -> Mock:
    return create_autospec(UsersClientABC)


@pytest.fixture
def merchants_client() -> Mock:
    return create_autospec(MerchantsClientABC)


@pytest.fixture
def offers_client() -> Mock:
    return create_autospec(OffersClientABC)


@pytest.fixture
def enforce_purchase_ownership() -> Mock:
    return Mock()


@pytest.fixture
def enforce_user_active() -> Mock:
    return Mock()


@pytest.fixture
def enforce_merchant_active() -> Mock:
    return Mock()


@pytest.fixture
def enforce_offer_available() -> Mock:
    return Mock()


@pytest.fixture
def enforce_currency_supported() -> Mock:
    return Mock()


@pytest.fixture
def purchase_service(
    purchase_repository: Mock,
    users_client: Mock,
    merchants_client: Mock,
    offers_client: Mock,
    enforce_purchase_ownership: Mock,
    enforce_user_active: Mock,
    enforce_merchant_active: Mock,
    enforce_offer_available: Mock,
    enforce_currency_supported: Mock,
) -> PurchaseService:
    return PurchaseService(
        repository=purchase_repository,
        users_client=users_client,
        merchants_client=merchants_client,
        offers_client=offers_client,
        enforce_purchase_ownership=enforce_purchase_ownership,
        enforce_user_active=enforce_user_active,
        enforce_merchant_active=enforce_merchant_active,
        enforce_offer_available=enforce_offer_available,
        enforce_currency_supported=enforce_currency_supported,
    )


def _make_ingest_data(**overrides: Any) -> dict[str, Any]:
    defaults: dict[str, Any] = {
        "external_id": "txn_test_001",
        "user_id": "b7e2c1a2-4f3a-4e2b-9c1a-8d2e3f4b5c6d",
        "merchant_id": "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d",
        "amount": Decimal("100.00"),
        "currency": "EUR",
    }
    defaults.update(overrides)
    return defaults


# Matches the default user_id in _make_ingest_data — used as the current_user_id argument
_CURRENT_USER_ID = "b7e2c1a2-4f3a-4e2b-9c1a-8d2e3f4b5c6d"


# ──────────────────────────────────────────────────────────────────────────────
# PurchaseService.ingest_purchase — happy path
# ──────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_ingest_purchase_returns_purchase_on_success(
    purchase_service: PurchaseService,
    purchase_repository: Mock,
    users_client: Mock,
    merchants_client: Mock,
    offers_client: Mock,
    purchase_factory: Callable[..., Purchase],
) -> None:
    # Arrange
    db = AsyncMock()
    new_purchase = purchase_factory()
    offer_mock = Mock(id="f0e1d2c3-b4a5-4678-9012-3456789abcde")

    purchase_repository.get_by_external_id.return_value = None
    users_client.get_user_by_id.return_value = Mock(active=True)
    merchants_client.get_merchant_by_id.return_value = Mock(active=True)
    offers_client.get_active_offer_for_merchant.return_value = offer_mock
    purchase_repository.add_purchase.return_value = new_purchase

    data = _make_ingest_data()

    # Act
    result = await purchase_service.ingest_purchase(data, _CURRENT_USER_ID, db)

    # Assert
    assert result == new_purchase
    purchase_repository.add_purchase.assert_called_once()


@pytest.mark.asyncio
async def test_ingest_purchase_stores_resolved_offer_id(
    purchase_service: PurchaseService,
    purchase_repository: Mock,
    users_client: Mock,
    merchants_client: Mock,
    offers_client: Mock,
    purchase_factory: Callable[..., Purchase],
) -> None:
    # Arrange
    db = AsyncMock()
    resolved_offer_id = "f0e1d2c3-b4a5-4678-9012-3456789abcde"
    offer_mock = Mock(id=resolved_offer_id)

    purchase_repository.get_by_external_id.return_value = None
    users_client.get_user_by_id.return_value = Mock(active=True)
    merchants_client.get_merchant_by_id.return_value = Mock(active=True)
    offers_client.get_active_offer_for_merchant.return_value = offer_mock
    purchase_repository.add_purchase.return_value = purchase_factory(
        offer_id=resolved_offer_id
    )

    # Act
    result = await purchase_service.ingest_purchase(
        _make_ingest_data(), _CURRENT_USER_ID, db
    )

    # Assert
    assert result.offer_id == resolved_offer_id


# ──────────────────────────────────────────────────────────────────────────────
# PurchaseService.ingest_purchase — duplicate detection
# ──────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_ingest_purchase_raises_on_duplicate_external_id(
    purchase_service: PurchaseService,
    purchase_repository: Mock,
    purchase_factory: Callable[..., Purchase],
) -> None:
    # Arrange
    db = AsyncMock()
    existing = purchase_factory(
        external_id="txn_test_001",
        amount=Decimal("100.00"),
        created_at=datetime(2026, 3, 1, 10, 0, 0),
    )
    purchase_repository.get_by_external_id.return_value = existing

    # Act & Assert
    with pytest.raises(DuplicatePurchaseException) as exc_info:
        await purchase_service.ingest_purchase(
            _make_ingest_data(), _CURRENT_USER_ID, db
        )

    assert exc_info.value.external_id == "txn_test_001"
    assert exc_info.value.amount == Decimal("100.00")


@pytest.mark.asyncio
async def test_ingest_purchase_does_not_call_repository_add_on_duplicate(
    purchase_service: PurchaseService,
    purchase_repository: Mock,
    purchase_factory: Callable[..., Purchase],
) -> None:
    # Arrange
    db = AsyncMock()
    purchase_repository.get_by_external_id.return_value = purchase_factory()

    # Act & Assert
    with pytest.raises(DuplicatePurchaseException):
        await purchase_service.ingest_purchase(
            _make_ingest_data(), _CURRENT_USER_ID, db
        )

    purchase_repository.add_purchase.assert_not_called()


# ──────────────────────────────────────────────────────────────────────────────
# PurchaseService.ingest_purchase — user policy delegation
# ──────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_ingest_purchase_raises_on_user_not_found(
    purchase_service: PurchaseService,
    purchase_repository: Mock,
    users_client: Mock,
    enforce_user_active: Mock,
) -> None:
    # Arrange
    db = AsyncMock()
    missing_user_id = "00000000-0000-0000-0000-000000000001"
    purchase_repository.get_by_external_id.return_value = None
    users_client.get_user_by_id.return_value = None
    enforce_user_active.side_effect = UserNotFoundException(missing_user_id)

    data = _make_ingest_data(user_id=missing_user_id)

    # Act & Assert
    with pytest.raises(UserNotFoundException) as exc_info:
        await purchase_service.ingest_purchase(data, _CURRENT_USER_ID, db)

    assert exc_info.value.user_id == missing_user_id


@pytest.mark.asyncio
async def test_ingest_purchase_raises_on_inactive_user(
    purchase_service: PurchaseService,
    purchase_repository: Mock,
    users_client: Mock,
    enforce_user_active: Mock,
) -> None:
    # Arrange
    db = AsyncMock()
    inactive_user_id = "b7e2c1a2-4f3a-4e2b-9c1a-8d2e3f4b5c6d"
    purchase_repository.get_by_external_id.return_value = None
    users_client.get_user_by_id.return_value = Mock(active=False)
    enforce_user_active.side_effect = UserInactiveException(inactive_user_id)

    # Act & Assert
    with pytest.raises(UserInactiveException):
        await purchase_service.ingest_purchase(
            _make_ingest_data(), _CURRENT_USER_ID, db
        )


# ──────────────────────────────────────────────────────────────────────────────
# PurchaseService.ingest_purchase — merchant policy delegation
# ──────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_ingest_purchase_raises_on_merchant_not_found(
    purchase_service: PurchaseService,
    purchase_repository: Mock,
    users_client: Mock,
    merchants_client: Mock,
    enforce_merchant_active: Mock,
) -> None:
    # Arrange
    db = AsyncMock()
    missing_merchant_id = "00000000-0000-0000-0000-000000000002"
    purchase_repository.get_by_external_id.return_value = None
    users_client.get_user_by_id.return_value = Mock(active=True)
    merchants_client.get_merchant_by_id.return_value = None
    enforce_merchant_active.side_effect = MerchantNotFoundException(missing_merchant_id)

    data = _make_ingest_data(merchant_id=missing_merchant_id)

    # Act & Assert
    with pytest.raises(MerchantNotFoundException) as exc_info:
        await purchase_service.ingest_purchase(data, _CURRENT_USER_ID, db)

    assert exc_info.value.merchant_id == missing_merchant_id


@pytest.mark.asyncio
async def test_ingest_purchase_raises_on_inactive_merchant(
    purchase_service: PurchaseService,
    purchase_repository: Mock,
    users_client: Mock,
    merchants_client: Mock,
    enforce_merchant_active: Mock,
) -> None:
    # Arrange
    db = AsyncMock()
    inactive_merchant_id = "a5b6c7d8-e9f0-4a1b-2c3d-4e5f6a7b8c9d"
    purchase_repository.get_by_external_id.return_value = None
    users_client.get_user_by_id.return_value = Mock(active=True)
    merchants_client.get_merchant_by_id.return_value = Mock(active=False)
    enforce_merchant_active.side_effect = MerchantInactiveException(
        inactive_merchant_id
    )

    data = _make_ingest_data(merchant_id=inactive_merchant_id)

    # Act & Assert
    with pytest.raises(MerchantInactiveException):
        await purchase_service.ingest_purchase(data, _CURRENT_USER_ID, db)


# ──────────────────────────────────────────────────────────────────────────────
# PurchaseService.ingest_purchase — offer policy delegation
# ──────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_ingest_purchase_raises_on_no_active_offer(
    purchase_service: PurchaseService,
    purchase_repository: Mock,
    users_client: Mock,
    merchants_client: Mock,
    offers_client: Mock,
    enforce_offer_available: Mock,
) -> None:
    # Arrange
    db = AsyncMock()
    merchant_id = "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d"
    purchase_repository.get_by_external_id.return_value = None
    users_client.get_user_by_id.return_value = Mock(active=True)
    merchants_client.get_merchant_by_id.return_value = Mock(active=True)
    offers_client.get_active_offer_for_merchant.return_value = None
    enforce_offer_available.side_effect = OfferNotAvailableException(merchant_id)

    # Act & Assert
    with pytest.raises(OfferNotAvailableException) as exc_info:
        await purchase_service.ingest_purchase(
            _make_ingest_data(), _CURRENT_USER_ID, db
        )

    assert exc_info.value.merchant_id == merchant_id


@pytest.mark.asyncio
async def test_ingest_purchase_queries_offer_with_todays_date(
    purchase_service: PurchaseService,
    purchase_repository: Mock,
    users_client: Mock,
    merchants_client: Mock,
    offers_client: Mock,
    purchase_factory: Callable[..., Purchase],
) -> None:
    # Arrange
    db = AsyncMock()
    offer_mock = Mock(id="f0e1d2c3-b4a5-4678-9012-3456789abcde")

    purchase_repository.get_by_external_id.return_value = None
    users_client.get_user_by_id.return_value = Mock(active=True)
    merchants_client.get_merchant_by_id.return_value = Mock(active=True)
    offers_client.get_active_offer_for_merchant.return_value = offer_mock
    purchase_repository.add_purchase.return_value = purchase_factory()

    # Act
    await purchase_service.ingest_purchase(_make_ingest_data(), _CURRENT_USER_ID, db)

    # Assert — the client was called with today's date for date-range validation
    call_args = offers_client.get_active_offer_for_merchant.call_args
    today_arg = call_args[0][2]  # third positional arg is `today`
    assert today_arg == date.today()


# ──────────────────────────────────────────────────────────────────────────────
# PurchaseService.ingest_purchase — currency policy delegation
# ──────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_ingest_purchase_raises_on_unsupported_currency(
    purchase_service: PurchaseService,
    purchase_repository: Mock,
    enforce_currency_supported: Mock,
) -> None:
    # Arrange
    db = AsyncMock()
    purchase_repository.get_by_external_id.return_value = None
    enforce_currency_supported.side_effect = UnsupportedCurrencyException("USD")

    # Act & Assert
    with pytest.raises(UnsupportedCurrencyException) as exc_info:
        await purchase_service.ingest_purchase(
            _make_ingest_data(currency="USD"), _CURRENT_USER_ID, db
        )

    assert exc_info.value.currency == "USD"


@pytest.mark.asyncio
async def test_ingest_purchase_does_not_call_clients_on_unsupported_currency(
    purchase_service: PurchaseService,
    purchase_repository: Mock,
    users_client: Mock,
    enforce_currency_supported: Mock,
) -> None:
    # Arrange
    db = AsyncMock()
    purchase_repository.get_by_external_id.return_value = None
    enforce_currency_supported.side_effect = UnsupportedCurrencyException("GBP")

    # Act & Assert
    with pytest.raises(UnsupportedCurrencyException):
        await purchase_service.ingest_purchase(
            _make_ingest_data(currency="GBP"), _CURRENT_USER_ID, db
        )

    users_client.get_user_by_id.assert_not_called()


# ──────────────────────────────────────────────────────────────────────────────
# PurchaseService.ingest_purchase — ownership policy delegation
# ──────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_ingest_purchase_raises_on_ownership_violation(
    purchase_service: PurchaseService,
    enforce_purchase_ownership: Mock,
) -> None:
    # Arrange
    db = AsyncMock()
    other_user_id = "00000000-0000-0000-0000-000000000099"
    enforce_purchase_ownership.side_effect = PurchaseOwnershipViolationException(
        _CURRENT_USER_ID, other_user_id
    )

    data = _make_ingest_data(user_id=other_user_id)

    # Act & Assert
    with pytest.raises(PurchaseOwnershipViolationException) as exc_info:
        await purchase_service.ingest_purchase(data, _CURRENT_USER_ID, db)

    assert exc_info.value.current_user_id == _CURRENT_USER_ID
    assert exc_info.value.requested_user_id == other_user_id


@pytest.mark.asyncio
async def test_ingest_purchase_does_not_check_duplicate_on_ownership_violation(
    purchase_service: PurchaseService,
    purchase_repository: Mock,
    enforce_purchase_ownership: Mock,
) -> None:
    # Arrange
    db = AsyncMock()
    other_user_id = "00000000-0000-0000-0000-000000000099"
    enforce_purchase_ownership.side_effect = PurchaseOwnershipViolationException(
        _CURRENT_USER_ID, other_user_id
    )

    data = _make_ingest_data(user_id=other_user_id)

    # Act & Assert
    with pytest.raises(PurchaseOwnershipViolationException):
        await purchase_service.ingest_purchase(data, _CURRENT_USER_ID, db)

    purchase_repository.get_by_external_id.assert_not_called()


# ──────────────────────────────────────────────────────────────────────────────
# PurchaseService.list_purchases
# ──────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_list_purchases_raises_on_invalid_status(
    purchase_service: PurchaseService,
    purchase_repository: Mock,
) -> None:
    # Arrange
    db = AsyncMock()
    invalid_status = "not_a_valid_status"

    # Act & Assert
    with pytest.raises(InvalidPurchaseStatusException) as exc_info:
        await purchase_service.list_purchases(
            db,
            status=invalid_status,
        )

    assert exc_info.value.status == invalid_status
    assert "not a valid purchase status" in str(exc_info.value)
