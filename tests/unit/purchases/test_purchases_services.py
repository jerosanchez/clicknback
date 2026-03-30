from datetime import date, datetime
from decimal import Decimal
from typing import Any, Callable
from unittest.mock import AsyncMock, Mock, create_autospec

import pytest

from app.core.broker import MessageBrokerABC
from app.core.events.purchase_events import PurchaseConfirmedByAdmin, PurchaseReversed
from app.purchases.clients import (
    CashbackClientABC,
    CashbackResultDTO,
    MerchantsClientABC,
    OffersClientABC,
    UsersClientABC,
    WalletsClientABC,
)
from app.purchases.exceptions import (
    DuplicatePurchaseException,
    InvalidPurchaseStatusException,
    MerchantInactiveException,
    MerchantNotFoundException,
    OfferNotAvailableException,
    PurchaseAlreadyReversedException,
    PurchaseNotFoundException,
    PurchaseNotPendingException,
    PurchaseOwnershipViolationException,
    PurchaseViewForbiddenException,
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
def wallets_client() -> Mock:
    return create_autospec(WalletsClientABC)


@pytest.fixture
def cashback_client() -> Mock:
    return create_autospec(CashbackClientABC)


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
def enforce_purchase_view_ownership() -> Mock:
    return Mock()


@pytest.fixture
def enforce_purchase_reversible() -> Mock:
    return Mock()


@pytest.fixture
def enforce_purchase_pending() -> Mock:
    return Mock()


@pytest.fixture
def broker() -> Mock:
    return create_autospec(MessageBrokerABC)


@pytest.fixture
def purchase_service(
    purchase_repository: Mock,
    cashback_client: Mock,
    wallets_client: Mock,
    users_client: Mock,
    merchants_client: Mock,
    offers_client: Mock,
    enforce_purchase_ownership: Mock,
    enforce_user_active: Mock,
    enforce_merchant_active: Mock,
    enforce_offer_available: Mock,
    enforce_currency_supported: Mock,
    enforce_purchase_view_ownership: Mock,
    enforce_purchase_reversible: Mock,
    enforce_purchase_pending: Mock,
    broker: Mock,
) -> PurchaseService:
    return PurchaseService(
        repository=purchase_repository,
        cashback_client=cashback_client,
        wallets_client=wallets_client,
        users_client=users_client,
        merchants_client=merchants_client,
        offers_client=offers_client,
        enforce_purchase_ownership=enforce_purchase_ownership,
        enforce_user_active=enforce_user_active,
        enforce_merchant_active=enforce_merchant_active,
        enforce_offer_available=enforce_offer_available,
        enforce_currency_supported=enforce_currency_supported,
        enforce_purchase_view_ownership=enforce_purchase_view_ownership,
        enforce_purchase_reversible=enforce_purchase_reversible,
        enforce_purchase_pending=enforce_purchase_pending,
        broker=broker,
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


def _make_uow() -> Mock:
    """Create a fresh mock UnitOfWork for ingest_purchase tests."""
    uow = Mock()
    uow.session = AsyncMock()
    uow.commit = AsyncMock()
    uow.rollback = AsyncMock()
    return uow


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
    uow = _make_uow()
    new_purchase = purchase_factory()
    offer_mock = Mock(
        id="f0e1d2c3-b4a5-4678-9012-3456789abcde", percentage=10.0, fixed_amount=None
    )

    purchase_repository.get_by_external_id.return_value = None
    users_client.get_user_by_id.return_value = Mock(active=True)
    merchants_client.get_merchant_by_id.return_value = Mock(active=True)
    offers_client.get_active_offer_for_merchant.return_value = offer_mock
    purchase_repository.add_purchase.return_value = new_purchase

    data = _make_ingest_data()

    # Act
    result = await purchase_service.ingest_purchase(data, _CURRENT_USER_ID, uow)

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
    uow = _make_uow()
    resolved_offer_id = "f0e1d2c3-b4a5-4678-9012-3456789abcde"
    offer_mock = Mock(id=resolved_offer_id, percentage=10.0, fixed_amount=None)

    purchase_repository.get_by_external_id.return_value = None
    users_client.get_user_by_id.return_value = Mock(active=True)
    merchants_client.get_merchant_by_id.return_value = Mock(active=True)
    offers_client.get_active_offer_for_merchant.return_value = offer_mock
    purchase_repository.add_purchase.return_value = purchase_factory(
        offer_id=resolved_offer_id
    )

    # Act
    result = await purchase_service.ingest_purchase(
        _make_ingest_data(), _CURRENT_USER_ID, uow
    )

    # Assert
    assert result.offer_id == resolved_offer_id


# ──────────────────────────────────────────────────────────────────────────────
# PurchaseService.ingest_purchase — UoW commit behaviour
# ──────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_ingest_purchase_commits_uow_on_success(
    purchase_service: PurchaseService,
    purchase_repository: Mock,
    wallets_client: Mock,
    users_client: Mock,
    merchants_client: Mock,
    offers_client: Mock,
    purchase_factory: Callable[..., Purchase],
) -> None:
    # Arrange
    uow = _make_uow()
    offer_mock = Mock(
        id="f0e1d2c3-b4a5-4678-9012-3456789abcde", percentage=10.0, fixed_amount=None
    )

    purchase_repository.get_by_external_id.return_value = None
    users_client.get_user_by_id.return_value = Mock(active=True)
    merchants_client.get_merchant_by_id.return_value = Mock(active=True)
    offers_client.get_active_offer_for_merchant.return_value = offer_mock
    purchase_repository.add_purchase.return_value = purchase_factory()

    # Act
    await purchase_service.ingest_purchase(_make_ingest_data(), _CURRENT_USER_ID, uow)

    # Assert
    uow.commit.assert_called_once()


@pytest.mark.asyncio
async def test_ingest_purchase_does_not_commit_uow_on_duplicate_error(
    purchase_service: PurchaseService,
    purchase_repository: Mock,
    purchase_factory: Callable[..., Purchase],
) -> None:
    # Arrange
    uow = _make_uow()
    purchase_repository.get_by_external_id.return_value = purchase_factory()

    # Act & Assert
    with pytest.raises(DuplicatePurchaseException):
        await purchase_service.ingest_purchase(
            _make_ingest_data(), _CURRENT_USER_ID, uow
        )

    uow.commit.assert_not_called()


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
    uow = _make_uow()
    existing = purchase_factory(
        external_id="txn_test_001",
        amount=Decimal("100.00"),
        created_at=datetime(2026, 3, 1, 10, 0, 0),
    )
    purchase_repository.get_by_external_id.return_value = existing

    # Act & Assert
    with pytest.raises(DuplicatePurchaseException) as exc_info:
        await purchase_service.ingest_purchase(
            _make_ingest_data(), _CURRENT_USER_ID, uow
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
    uow = _make_uow()
    purchase_repository.get_by_external_id.return_value = purchase_factory()

    # Act & Assert
    with pytest.raises(DuplicatePurchaseException):
        await purchase_service.ingest_purchase(
            _make_ingest_data(), _CURRENT_USER_ID, uow
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
    uow = _make_uow()
    missing_user_id = "00000000-0000-0000-0000-000000000001"
    purchase_repository.get_by_external_id.return_value = None
    users_client.get_user_by_id.return_value = None
    enforce_user_active.side_effect = UserNotFoundException(missing_user_id)

    data = _make_ingest_data(user_id=missing_user_id)

    # Act & Assert
    with pytest.raises(UserNotFoundException) as exc_info:
        await purchase_service.ingest_purchase(data, _CURRENT_USER_ID, uow)

    assert exc_info.value.user_id == missing_user_id


@pytest.mark.asyncio
async def test_ingest_purchase_raises_on_inactive_user(
    purchase_service: PurchaseService,
    purchase_repository: Mock,
    users_client: Mock,
    enforce_user_active: Mock,
) -> None:
    # Arrange
    uow = _make_uow()
    inactive_user_id = "b7e2c1a2-4f3a-4e2b-9c1a-8d2e3f4b5c6d"
    purchase_repository.get_by_external_id.return_value = None
    users_client.get_user_by_id.return_value = Mock(active=False)
    enforce_user_active.side_effect = UserInactiveException(inactive_user_id)

    # Act & Assert
    with pytest.raises(UserInactiveException):
        await purchase_service.ingest_purchase(
            _make_ingest_data(), _CURRENT_USER_ID, uow
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
    uow = _make_uow()
    missing_merchant_id = "00000000-0000-0000-0000-000000000002"
    purchase_repository.get_by_external_id.return_value = None
    users_client.get_user_by_id.return_value = Mock(active=True)
    merchants_client.get_merchant_by_id.return_value = None
    enforce_merchant_active.side_effect = MerchantNotFoundException(missing_merchant_id)

    data = _make_ingest_data(merchant_id=missing_merchant_id)

    # Act & Assert
    with pytest.raises(MerchantNotFoundException) as exc_info:
        await purchase_service.ingest_purchase(data, _CURRENT_USER_ID, uow)

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
    uow = _make_uow()
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
        await purchase_service.ingest_purchase(data, _CURRENT_USER_ID, uow)


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
    uow = _make_uow()
    merchant_id = "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d"
    purchase_repository.get_by_external_id.return_value = None
    users_client.get_user_by_id.return_value = Mock(active=True)
    merchants_client.get_merchant_by_id.return_value = Mock(active=True)
    offers_client.get_active_offer_for_merchant.return_value = None
    enforce_offer_available.side_effect = OfferNotAvailableException(merchant_id)

    # Act & Assert
    with pytest.raises(OfferNotAvailableException) as exc_info:
        await purchase_service.ingest_purchase(
            _make_ingest_data(), _CURRENT_USER_ID, uow
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
    uow = _make_uow()
    offer_mock = Mock(
        id="f0e1d2c3-b4a5-4678-9012-3456789abcde", percentage=10.0, fixed_amount=None
    )

    purchase_repository.get_by_external_id.return_value = None
    users_client.get_user_by_id.return_value = Mock(active=True)
    merchants_client.get_merchant_by_id.return_value = Mock(active=True)
    offers_client.get_active_offer_for_merchant.return_value = offer_mock
    purchase_repository.add_purchase.return_value = purchase_factory()

    # Act
    await purchase_service.ingest_purchase(_make_ingest_data(), _CURRENT_USER_ID, uow)

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
    uow = _make_uow()
    purchase_repository.get_by_external_id.return_value = None
    enforce_currency_supported.side_effect = UnsupportedCurrencyException("USD")

    # Act & Assert
    with pytest.raises(UnsupportedCurrencyException) as exc_info:
        await purchase_service.ingest_purchase(
            _make_ingest_data(currency="USD"), _CURRENT_USER_ID, uow
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
    uow = _make_uow()
    purchase_repository.get_by_external_id.return_value = None
    enforce_currency_supported.side_effect = UnsupportedCurrencyException("GBP")

    # Act & Assert
    with pytest.raises(UnsupportedCurrencyException):
        await purchase_service.ingest_purchase(
            _make_ingest_data(currency="GBP"), _CURRENT_USER_ID, uow
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
    uow = _make_uow()
    other_user_id = "00000000-0000-0000-0000-000000000099"
    enforce_purchase_ownership.side_effect = PurchaseOwnershipViolationException(
        _CURRENT_USER_ID, other_user_id
    )

    data = _make_ingest_data(user_id=other_user_id)

    # Act & Assert
    with pytest.raises(PurchaseOwnershipViolationException) as exc_info:
        await purchase_service.ingest_purchase(data, _CURRENT_USER_ID, uow)

    assert exc_info.value.current_user_id == _CURRENT_USER_ID
    assert exc_info.value.requested_user_id == other_user_id


@pytest.mark.asyncio
async def test_ingest_purchase_does_not_check_duplicate_on_ownership_violation(
    purchase_service: PurchaseService,
    purchase_repository: Mock,
    enforce_purchase_ownership: Mock,
) -> None:
    # Arrange
    uow = _make_uow()
    other_user_id = "00000000-0000-0000-0000-000000000099"
    enforce_purchase_ownership.side_effect = PurchaseOwnershipViolationException(
        _CURRENT_USER_ID, other_user_id
    )

    data = _make_ingest_data(user_id=other_user_id)

    # Act & Assert
    with pytest.raises(PurchaseOwnershipViolationException):
        await purchase_service.ingest_purchase(data, _CURRENT_USER_ID, uow)

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


# ──────────────────────────────────────────────────────────────────────────────
# PurchaseService.get_purchase_details — happy path
# ──────────────────────────────────────────────────────────────────────────────

_DETAIL_PURCHASE_ID = "aa000001-0000-0000-0000-000000000001"
_DETAIL_CURRENT_USER_ID = "b7e2c1a2-4f3a-4e2b-9c1a-8d2e3f4b5c6d"
_DETAIL_MERCHANT_NAME = "Shoply"


@pytest.mark.asyncio
async def test_get_purchase_details_returns_purchase_and_merchant_name_on_success(
    purchase_service: PurchaseService,
    purchase_repository: Mock,
    merchants_client: Mock,
    purchase_factory: Callable[..., Purchase],
) -> None:
    # Arrange
    db = AsyncMock()
    purchase = purchase_factory(
        id=_DETAIL_PURCHASE_ID,
        user_id=_DETAIL_CURRENT_USER_ID,
    )
    purchase_repository.get_by_id.return_value = purchase
    merchant_mock = Mock()
    merchant_mock.name = _DETAIL_MERCHANT_NAME
    merchants_client.get_merchant_by_id.return_value = merchant_mock

    # Act
    result_purchase, result_name = await purchase_service.get_purchase_details(
        _DETAIL_PURCHASE_ID, _DETAIL_CURRENT_USER_ID, db
    )

    # Assert
    assert result_purchase == purchase
    assert result_name == _DETAIL_MERCHANT_NAME


@pytest.mark.asyncio
async def test_get_purchase_details_falls_back_to_unknown_when_merchant_missing(
    purchase_service: PurchaseService,
    purchase_repository: Mock,
    merchants_client: Mock,
    purchase_factory: Callable[..., Purchase],
) -> None:
    # Arrange
    db = AsyncMock()
    purchase = purchase_factory(
        id=_DETAIL_PURCHASE_ID,
        user_id=_DETAIL_CURRENT_USER_ID,
    )
    purchase_repository.get_by_id.return_value = purchase
    merchants_client.get_merchant_by_id.return_value = None

    # Act
    _, result_name = await purchase_service.get_purchase_details(
        _DETAIL_PURCHASE_ID, _DETAIL_CURRENT_USER_ID, db
    )

    # Assert
    assert result_name == "Unknown"


# ──────────────────────────────────────────────────────────────────────────────
# PurchaseService.get_purchase_details — not found
# ──────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_purchase_details_raises_on_purchase_not_found(
    purchase_service: PurchaseService,
    purchase_repository: Mock,
) -> None:
    # Arrange
    db = AsyncMock()
    missing_purchase_id = "00000000-0000-0000-0000-000000000000"
    purchase_repository.get_by_id.return_value = None

    # Act & Assert
    with pytest.raises(PurchaseNotFoundException) as exc_info:
        await purchase_service.get_purchase_details(
            missing_purchase_id, _DETAIL_CURRENT_USER_ID, db
        )

    assert exc_info.value.purchase_id == missing_purchase_id


@pytest.mark.asyncio
async def test_get_purchase_details_does_not_check_ownership_when_not_found(
    purchase_service: PurchaseService,
    purchase_repository: Mock,
    enforce_purchase_view_ownership: Mock,
) -> None:
    # Arrange
    db = AsyncMock()
    purchase_repository.get_by_id.return_value = None

    # Act & Assert
    with pytest.raises(PurchaseNotFoundException):
        await purchase_service.get_purchase_details(
            "00000000-0000-0000-0000-000000000000", _DETAIL_CURRENT_USER_ID, db
        )

    enforce_purchase_view_ownership.assert_not_called()


# ──────────────────────────────────────────────────────────────────────────────
# PurchaseService.get_purchase_details — ownership enforcement
# ──────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_purchase_details_raises_on_ownership_violation(
    purchase_service: PurchaseService,
    purchase_repository: Mock,
    enforce_purchase_view_ownership: Mock,
    purchase_factory: Callable[..., Purchase],
) -> None:
    # Arrange
    db = AsyncMock()
    other_user_id = "c8d3e2b1-5a4b-4c3d-8b2a-7e6f5d4c3b2a"
    purchase = purchase_factory(
        id=_DETAIL_PURCHASE_ID,
        user_id=other_user_id,
    )
    purchase_repository.get_by_id.return_value = purchase
    enforce_purchase_view_ownership.side_effect = PurchaseViewForbiddenException(
        _DETAIL_PURCHASE_ID, other_user_id, _DETAIL_CURRENT_USER_ID
    )

    # Act & Assert
    with pytest.raises(PurchaseViewForbiddenException) as exc_info:
        await purchase_service.get_purchase_details(
            _DETAIL_PURCHASE_ID, _DETAIL_CURRENT_USER_ID, db
        )

    assert exc_info.value.purchase_id == _DETAIL_PURCHASE_ID
    assert exc_info.value.resource_owner_id == other_user_id
    assert exc_info.value.current_user_id == _DETAIL_CURRENT_USER_ID


@pytest.mark.asyncio
async def test_get_purchase_details_calls_ownership_check_with_correct_args(
    purchase_service: PurchaseService,
    purchase_repository: Mock,
    merchants_client: Mock,
    enforce_purchase_view_ownership: Mock,
    purchase_factory: Callable[..., Purchase],
) -> None:
    # Arrange
    db = AsyncMock()
    purchase = purchase_factory(
        id=_DETAIL_PURCHASE_ID,
        user_id=_DETAIL_CURRENT_USER_ID,
    )
    purchase_repository.get_by_id.return_value = purchase
    merchant_mock = Mock()
    merchant_mock.name = _DETAIL_MERCHANT_NAME
    merchants_client.get_merchant_by_id.return_value = merchant_mock

    # Act
    await purchase_service.get_purchase_details(
        _DETAIL_PURCHASE_ID, _DETAIL_CURRENT_USER_ID, db
    )

    # Assert
    enforce_purchase_view_ownership.assert_called_once_with(
        _DETAIL_CURRENT_USER_ID, purchase.user_id, _DETAIL_PURCHASE_ID
    )


# ──────────────────────────────────────────────────────────────────────────────
# PurchaseService.list_user_purchases — happy path
# ──────────────────────────────────────────────────────────────────────────────

_LIST_USER_ID = "b7e2c1a2-4f3a-4e2b-9c1a-8d2e3f4b5c6d"
_LIST_MERCHANT_ID = "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d"
_LIST_MERCHANT_NAME = "Shoply"


@pytest.mark.asyncio
async def test_list_user_purchases_returns_enriched_purchases(
    purchase_service: PurchaseService,
    purchase_repository: Mock,
    merchants_client: Mock,
    purchase_factory: Callable[..., Purchase],
) -> None:
    # Arrange
    db = AsyncMock()
    purchase = purchase_factory(user_id=_LIST_USER_ID, merchant_id=_LIST_MERCHANT_ID)
    purchase_repository.list_purchases.return_value = ([purchase], 1)
    merchant_mock = Mock()
    merchant_mock.name = _LIST_MERCHANT_NAME
    merchants_client.get_merchants_by_ids.return_value = {
        _LIST_MERCHANT_ID: merchant_mock
    }

    # Act
    enriched, total = await purchase_service.list_user_purchases(db, _LIST_USER_ID)

    # Assert
    assert total == 1
    assert len(enriched) == 1
    result_purchase, result_name = enriched[0]
    assert result_purchase == purchase
    assert result_name == _LIST_MERCHANT_NAME


@pytest.mark.asyncio
async def test_list_user_purchases_returns_empty_list_when_no_purchases(
    purchase_service: PurchaseService,
    purchase_repository: Mock,
    merchants_client: Mock,
) -> None:
    # Arrange
    db = AsyncMock()
    purchase_repository.list_purchases.return_value = ([], 0)
    merchants_client.get_merchants_by_ids.return_value = {}

    # Act
    enriched, total = await purchase_service.list_user_purchases(db, _LIST_USER_ID)

    # Assert
    assert total == 0
    assert enriched == []


@pytest.mark.asyncio
async def test_list_user_purchases_batch_loads_merchants_in_one_call(
    purchase_service: PurchaseService,
    purchase_repository: Mock,
    merchants_client: Mock,
    purchase_factory: Callable[..., Purchase],
) -> None:
    """Verifies batch loading: get_merchants_by_ids is called once with all IDs."""
    # Arrange
    db = AsyncMock()
    merchant_id_a = "aaaa0000-0000-0000-0000-000000000001"
    merchant_id_b = "bbbb0000-0000-0000-0000-000000000002"
    purchases = [
        purchase_factory(merchant_id=merchant_id_a),
        purchase_factory(merchant_id=merchant_id_b),
        purchase_factory(merchant_id=merchant_id_a),  # same merchant as first
    ]
    purchase_repository.list_purchases.return_value = (purchases, 3)
    merchant_a = Mock()
    merchant_a.name = "Alpha"
    merchant_b = Mock()
    merchant_b.name = "Beta"
    merchants_client.get_merchants_by_ids.return_value = {
        merchant_id_a: merchant_a,
        merchant_id_b: merchant_b,
    }

    # Act
    await purchase_service.list_user_purchases(db, _LIST_USER_ID)

    # Assert — batch method called exactly once (not once per purchase)
    merchants_client.get_merchants_by_ids.assert_called_once()
    called_ids = set(merchants_client.get_merchants_by_ids.call_args[0][1])
    assert called_ids == {merchant_id_a, merchant_id_b}


@pytest.mark.asyncio
async def test_list_user_purchases_falls_back_to_unknown_when_merchant_missing(
    purchase_service: PurchaseService,
    purchase_repository: Mock,
    merchants_client: Mock,
    purchase_factory: Callable[..., Purchase],
) -> None:
    # Arrange
    db = AsyncMock()
    known_id = "aaaa0000-0000-0000-0000-000000000001"
    unknown_id = "ffff0000-0000-0000-0000-000000000099"
    purchases = [
        purchase_factory(merchant_id=known_id),
        purchase_factory(merchant_id=unknown_id),
    ]
    purchase_repository.list_purchases.return_value = (purchases, 2)
    # Only the known merchant is returned from the batch query
    known_merchant_mock = Mock()
    known_merchant_mock.name = "KnownShop"
    merchants_client.get_merchants_by_ids.return_value = {known_id: known_merchant_mock}

    # Act
    enriched, _ = await purchase_service.list_user_purchases(db, _LIST_USER_ID)

    # Assert
    names = [name for _, name in enriched]
    assert names[0] == "KnownShop"
    assert names[1] == "Unknown"


@pytest.mark.asyncio
async def test_list_user_purchases_filters_by_current_user(
    purchase_service: PurchaseService,
    purchase_repository: Mock,
    merchants_client: Mock,
) -> None:
    # Arrange
    db = AsyncMock()
    purchase_repository.list_purchases.return_value = ([], 0)
    merchants_client.get_merchants_by_ids.return_value = {}

    # Act
    await purchase_service.list_user_purchases(db, _LIST_USER_ID)

    # Assert — repository is called with the user's own ID as filter
    call_kwargs = purchase_repository.list_purchases.call_args[1]
    assert call_kwargs["user_id"] == _LIST_USER_ID


# ──────────────────────────────────────────────────────────────────────────────
# PurchaseService.list_user_purchases — status validation
# ──────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_list_user_purchases_raises_on_invalid_status(
    purchase_service: PurchaseService,
    purchase_repository: Mock,
) -> None:
    # Arrange
    db = AsyncMock()

    # Act & Assert
    with pytest.raises(InvalidPurchaseStatusException) as exc_info:
        await purchase_service.list_user_purchases(
            db, _LIST_USER_ID, status="not_a_valid_status"
        )

    assert exc_info.value.status == "not_a_valid_status"


# ──────────────────────────────────────────────────────────────────────────────
# PurchaseService.ingest_purchase — wallet balance
# ──────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_ingest_purchase_credits_wallet_with_cashback_clients_amount(
    purchase_service: PurchaseService,
    purchase_repository: Mock,
    cashback_client: Mock,
    wallets_client: Mock,
    users_client: Mock,
    merchants_client: Mock,
    offers_client: Mock,
    purchase_factory: Callable[..., Purchase],
) -> None:
    # Arrange
    uow = _make_uow()
    offer_mock = Mock(
        id="f0e1d2c3-b4a5-4678-9012-3456789abcde", percentage=10.0, fixed_amount=None
    )
    expected_cashback = Decimal("10.00")
    cashback_client.calculate.return_value = CashbackResultDTO(
        offer_id=offer_mock.id, cashback_amount=expected_cashback
    )

    purchase_repository.get_by_external_id.return_value = None
    users_client.get_user_by_id.return_value = Mock(active=True)
    merchants_client.get_merchant_by_id.return_value = Mock(active=True)
    offers_client.get_active_offer_for_merchant.return_value = offer_mock
    purchase_repository.add_purchase.return_value = purchase_factory()

    # Act
    await purchase_service.ingest_purchase(
        _make_ingest_data(amount=Decimal("100.00")), _CURRENT_USER_ID, uow
    )

    # Assert — wallet receives exactly the amount returned by the cashback client
    wallets_client.credit_pending.assert_called_once_with(
        uow.session, _CURRENT_USER_ID, expected_cashback
    )


@pytest.mark.asyncio
async def test_ingest_purchase_delegates_calculation_to_cashback_client(
    purchase_service: PurchaseService,
    purchase_repository: Mock,
    cashback_client: Mock,
    users_client: Mock,
    merchants_client: Mock,
    offers_client: Mock,
    purchase_factory: Callable[..., Purchase],
) -> None:
    # Arrange
    uow = _make_uow()
    offer_id = "f0e1d2c3-b4a5-4678-9012-3456789abcde"
    percentage = 10.0
    fixed_amount = None
    purchase_amount = Decimal("100.00")
    offer_mock = Mock(id=offer_id, percentage=percentage, fixed_amount=fixed_amount)
    cashback_client.calculate.return_value = CashbackResultDTO(
        offer_id=offer_id, cashback_amount=Decimal("10.00")
    )

    purchase_repository.get_by_external_id.return_value = None
    users_client.get_user_by_id.return_value = Mock(active=True)
    merchants_client.get_merchant_by_id.return_value = Mock(active=True)
    offers_client.get_active_offer_for_merchant.return_value = offer_mock
    purchase_repository.add_purchase.return_value = purchase_factory()

    # Act
    await purchase_service.ingest_purchase(
        _make_ingest_data(amount=purchase_amount), _CURRENT_USER_ID, uow
    )

    # Assert — cashback client called with the resolved offer details
    cashback_client.calculate.assert_called_once_with(
        offer_id=offer_id,
        percentage=percentage,
        fixed_amount=fixed_amount,
        purchase_amount=purchase_amount,
    )


@pytest.mark.asyncio
async def test_ingest_purchase_uses_fixed_amount_cashback_when_available(
    purchase_service: PurchaseService,
    purchase_repository: Mock,
    cashback_client: Mock,
    wallets_client: Mock,
    users_client: Mock,
    merchants_client: Mock,
    offers_client: Mock,
    purchase_factory: Callable[..., Purchase],
) -> None:
    # Arrange
    uow = _make_uow()
    offer_id = "f0e1d2c3-b4a5-4678-9012-3456789abcde"
    fixed_amount = 5.0
    fixed_offer = Mock(id=offer_id, percentage=10.0, fixed_amount=fixed_amount)
    expected_cashback = Decimal("5.00")
    cashback_client.calculate.return_value = CashbackResultDTO(
        offer_id=offer_id, cashback_amount=expected_cashback
    )

    purchase_repository.get_by_external_id.return_value = None
    users_client.get_user_by_id.return_value = Mock(active=True)
    merchants_client.get_merchant_by_id.return_value = Mock(active=True)
    offers_client.get_active_offer_for_merchant.return_value = fixed_offer
    purchase_repository.add_purchase.return_value = purchase_factory()

    # Act
    await purchase_service.ingest_purchase(
        _make_ingest_data(amount=Decimal("200.00")), _CURRENT_USER_ID, uow
    )

    # Assert — service passes cashback client's result to wallet; does not recalculate
    wallets_client.credit_pending.assert_called_once_with(
        uow.session, _CURRENT_USER_ID, expected_cashback
    )


@pytest.mark.asyncio
async def test_ingest_purchase_wallet_not_credited_on_failure(
    purchase_service: PurchaseService,
    purchase_repository: Mock,
    wallets_client: Mock,
    purchase_factory: Callable[..., Purchase],
) -> None:
    # Arrange
    db = AsyncMock()
    existing = purchase_factory(external_id="txn_test_001")
    purchase_repository.get_by_external_id.return_value = existing

    # Act & Assert
    with pytest.raises(DuplicatePurchaseException):
        await purchase_service.ingest_purchase(
            _make_ingest_data(), _CURRENT_USER_ID, db
        )

    wallets_client.credit_pending.assert_not_called()


# ──────────────────────────────────────────────────────────────────────────────
# PurchaseService.ingest_purchase — cashback transaction
# ──────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_ingest_purchase_creates_cashback_transaction_on_success(
    purchase_service: PurchaseService,
    purchase_repository: Mock,
    cashback_client: Mock,
    users_client: Mock,
    merchants_client: Mock,
    offers_client: Mock,
    purchase_factory: Callable[..., Purchase],
) -> None:
    # Arrange
    uow = _make_uow()
    offer_mock = Mock(
        id="f0e1d2c3-b4a5-4678-9012-3456789abcde", percentage=10.0, fixed_amount=None
    )
    expected_cashback = Decimal("10.00")
    cashback_client.calculate.return_value = CashbackResultDTO(
        offer_id=offer_mock.id, cashback_amount=expected_cashback
    )
    new_purchase = purchase_factory()

    purchase_repository.get_by_external_id.return_value = None
    users_client.get_user_by_id.return_value = Mock(active=True)
    merchants_client.get_merchant_by_id.return_value = Mock(active=True)
    offers_client.get_active_offer_for_merchant.return_value = offer_mock
    purchase_repository.add_purchase.return_value = new_purchase

    # Act
    await purchase_service.ingest_purchase(
        _make_ingest_data(amount=Decimal("100.00")), _CURRENT_USER_ID, uow
    )

    # Assert — cashback transaction created with purchase id, user id, and calculated amount
    cashback_client.create.assert_called_once_with(
        uow.session, new_purchase.id, _CURRENT_USER_ID, expected_cashback
    )


@pytest.mark.asyncio
async def test_ingest_purchase_cashback_transaction_not_created_on_failure(
    purchase_service: PurchaseService,
    purchase_repository: Mock,
    cashback_client: Mock,
    purchase_factory: Callable[..., Purchase],
) -> None:
    # Arrange
    uow = _make_uow()
    purchase_repository.get_by_external_id.return_value = purchase_factory(
        external_id="txn_test_001"
    )

    # Act & Assert
    with pytest.raises(DuplicatePurchaseException):
        await purchase_service.ingest_purchase(
            _make_ingest_data(), _CURRENT_USER_ID, uow
        )

    cashback_client.create.assert_not_called()


# ──────────────────────────────────────────────────────────────────────────────
# PurchaseService.reverse_purchase — happy path
# ──────────────────────────────────────────────────────────────────────────────

_REVERSE_PURCHASE_ID = "aa000001-0000-0000-0000-000000000001"
_REVERSE_ADMIN_ID = "d9f4b3c2-6b5c-5d4e-7c3b-6a5e4d3c2b1a"
_REVERSE_USER_ID = "b7e2c1a2-4f3a-4e2b-9c1a-8d2e3f4b5c6d"


@pytest.mark.asyncio
async def test_reverse_purchase_returns_reversed_purchase_on_success(
    purchase_service: PurchaseService,
    purchase_repository: Mock,
    purchase_factory: Callable[..., Purchase],
) -> None:
    # Arrange
    uow = _make_uow()
    cashback_amount = Decimal("5.00")
    original_purchase = purchase_factory(
        id=_REVERSE_PURCHASE_ID,
        user_id=_REVERSE_USER_ID,
        cashback_amount=cashback_amount,
        status="pending",
    )
    reversed_purchase = purchase_factory(
        id=_REVERSE_PURCHASE_ID,
        user_id=_REVERSE_USER_ID,
        cashback_amount=Decimal("0"),
        status="reversed",
    )
    purchase_repository.get_by_id.return_value = original_purchase
    purchase_repository.reverse_purchase.return_value = reversed_purchase

    # Act
    result = await purchase_service.reverse_purchase(
        _REVERSE_PURCHASE_ID, _REVERSE_ADMIN_ID, uow
    )

    # Assert
    assert result.status == "reversed"
    assert result.cashback_amount == Decimal("0")


@pytest.mark.asyncio
async def test_reverse_purchase_commits_uow_on_success(
    purchase_service: PurchaseService,
    purchase_repository: Mock,
    purchase_factory: Callable[..., Purchase],
) -> None:
    # Arrange
    uow = _make_uow()
    original_purchase = purchase_factory(
        id=_REVERSE_PURCHASE_ID,
        user_id=_REVERSE_USER_ID,
        cashback_amount=Decimal("5.00"),
        status="pending",
    )
    purchase_repository.get_by_id.return_value = original_purchase
    purchase_repository.reverse_purchase.return_value = purchase_factory(
        status="reversed", cashback_amount=Decimal("0")
    )

    # Act
    await purchase_service.reverse_purchase(
        _REVERSE_PURCHASE_ID, _REVERSE_ADMIN_ID, uow
    )

    # Assert
    uow.commit.assert_called_once()


@pytest.mark.asyncio
async def test_reverse_purchase_deducts_from_pending_balance_for_pending_purchase(
    purchase_service: PurchaseService,
    purchase_repository: Mock,
    wallets_client: Mock,
    purchase_factory: Callable[..., Purchase],
) -> None:
    # Arrange
    uow = _make_uow()
    cashback_amount = Decimal("5.00")
    original_purchase = purchase_factory(
        id=_REVERSE_PURCHASE_ID,
        user_id=_REVERSE_USER_ID,
        cashback_amount=cashback_amount,
        status="pending",
    )
    purchase_repository.get_by_id.return_value = original_purchase
    purchase_repository.reverse_purchase.return_value = purchase_factory(
        status="reversed", cashback_amount=Decimal("0")
    )

    # Act
    await purchase_service.reverse_purchase(
        _REVERSE_PURCHASE_ID, _REVERSE_ADMIN_ID, uow
    )

    # Assert — pending balance decremented, available balance NOT touched
    wallets_client.reverse_pending.assert_called_once_with(
        uow.session, _REVERSE_USER_ID, cashback_amount
    )
    wallets_client.reverse_available.assert_not_called()


@pytest.mark.asyncio
async def test_reverse_purchase_deducts_from_available_balance_for_confirmed_purchase(
    purchase_service: PurchaseService,
    purchase_repository: Mock,
    wallets_client: Mock,
    purchase_factory: Callable[..., Purchase],
) -> None:
    # Arrange
    uow = _make_uow()
    cashback_amount = Decimal("15.00")
    original_purchase = purchase_factory(
        id=_REVERSE_PURCHASE_ID,
        user_id=_REVERSE_USER_ID,
        cashback_amount=cashback_amount,
        status="confirmed",
    )
    purchase_repository.get_by_id.return_value = original_purchase
    purchase_repository.reverse_purchase.return_value = purchase_factory(
        status="reversed", cashback_amount=Decimal("0")
    )

    # Act
    await purchase_service.reverse_purchase(
        _REVERSE_PURCHASE_ID, _REVERSE_ADMIN_ID, uow
    )

    # Assert — available balance decremented, pending balance NOT touched
    wallets_client.reverse_available.assert_called_once_with(
        uow.session, _REVERSE_USER_ID, cashback_amount
    )
    wallets_client.reverse_pending.assert_not_called()


@pytest.mark.asyncio
async def test_reverse_purchase_calls_cashback_reverse(
    purchase_service: PurchaseService,
    purchase_repository: Mock,
    cashback_client: Mock,
    purchase_factory: Callable[..., Purchase],
) -> None:
    # Arrange
    uow = _make_uow()
    original_purchase = purchase_factory(
        id=_REVERSE_PURCHASE_ID,
        user_id=_REVERSE_USER_ID,
        cashback_amount=Decimal("5.00"),
        status="pending",
    )
    purchase_repository.get_by_id.return_value = original_purchase
    purchase_repository.reverse_purchase.return_value = purchase_factory(
        status="reversed", cashback_amount=Decimal("0")
    )

    # Act
    await purchase_service.reverse_purchase(
        _REVERSE_PURCHASE_ID, _REVERSE_ADMIN_ID, uow
    )

    # Assert — cashback.reverse called with correct session and purchase_id
    cashback_client.reverse.assert_called_once_with(uow.session, _REVERSE_PURCHASE_ID)


@pytest.mark.asyncio
async def test_reverse_purchase_publishes_domain_event_on_success(
    purchase_service: PurchaseService,
    purchase_repository: Mock,
    broker: Mock,
    purchase_factory: Callable[..., Purchase],
) -> None:
    # Arrange
    uow = _make_uow()
    original_purchase = purchase_factory(
        id=_REVERSE_PURCHASE_ID,
        user_id=_REVERSE_USER_ID,
        cashback_amount=Decimal("5.00"),
        status="pending",
    )
    purchase_repository.get_by_id.return_value = original_purchase
    purchase_repository.reverse_purchase.return_value = purchase_factory(
        status="reversed", cashback_amount=Decimal("0")
    )

    # Act
    await purchase_service.reverse_purchase(
        _REVERSE_PURCHASE_ID, _REVERSE_ADMIN_ID, uow
    )

    # Assert
    broker.publish.assert_called_once()
    event = broker.publish.call_args[0][0]
    assert isinstance(event, PurchaseReversed)
    assert event.purchase_id == _REVERSE_PURCHASE_ID
    assert event.admin_id == _REVERSE_ADMIN_ID


# ──────────────────────────────────────────────────────────────────────────────
# PurchaseService.reverse_purchase — not found
# ──────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_reverse_purchase_raises_on_purchase_not_found(
    purchase_service: PurchaseService,
    purchase_repository: Mock,
) -> None:
    # Arrange
    uow = _make_uow()
    missing_id = "00000000-0000-0000-0000-000000000000"
    purchase_repository.get_by_id.return_value = None

    # Act & Assert
    with pytest.raises(PurchaseNotFoundException) as exc_info:
        await purchase_service.reverse_purchase(missing_id, _REVERSE_ADMIN_ID, uow)

    assert exc_info.value.purchase_id == missing_id


@pytest.mark.asyncio
async def test_reverse_purchase_does_not_commit_uow_on_not_found(
    purchase_service: PurchaseService,
    purchase_repository: Mock,
) -> None:
    # Arrange
    uow = _make_uow()
    purchase_repository.get_by_id.return_value = None

    # Act & Assert
    with pytest.raises(PurchaseNotFoundException):
        await purchase_service.reverse_purchase(
            "00000000-0000-0000-0000-000000000000", _REVERSE_ADMIN_ID, uow
        )

    uow.commit.assert_not_called()


# ──────────────────────────────────────────────────────────────────────────────
# PurchaseService.reverse_purchase — already reversed
# ──────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_reverse_purchase_raises_on_already_reversed(
    purchase_service: PurchaseService,
    purchase_repository: Mock,
    enforce_purchase_reversible: Mock,
    purchase_factory: Callable[..., Purchase],
) -> None:
    # Arrange
    uow = _make_uow()
    already_reversed = purchase_factory(
        id=_REVERSE_PURCHASE_ID,
        user_id=_REVERSE_USER_ID,
        status="reversed",
    )
    purchase_repository.get_by_id.return_value = already_reversed
    enforce_purchase_reversible.side_effect = PurchaseAlreadyReversedException(
        _REVERSE_PURCHASE_ID
    )

    # Act & Assert
    with pytest.raises(PurchaseAlreadyReversedException) as exc_info:
        await purchase_service.reverse_purchase(
            _REVERSE_PURCHASE_ID, _REVERSE_ADMIN_ID, uow
        )

    assert exc_info.value.purchase_id == _REVERSE_PURCHASE_ID


@pytest.mark.asyncio
async def test_reverse_purchase_does_not_commit_uow_on_already_reversed(
    purchase_service: PurchaseService,
    purchase_repository: Mock,
    enforce_purchase_reversible: Mock,
    purchase_factory: Callable[..., Purchase],
) -> None:
    # Arrange
    uow = _make_uow()
    already_reversed = purchase_factory(
        id=_REVERSE_PURCHASE_ID, user_id=_REVERSE_USER_ID, status="reversed"
    )
    purchase_repository.get_by_id.return_value = already_reversed
    enforce_purchase_reversible.side_effect = PurchaseAlreadyReversedException(
        _REVERSE_PURCHASE_ID
    )

    # Act & Assert
    with pytest.raises(PurchaseAlreadyReversedException):
        await purchase_service.reverse_purchase(
            _REVERSE_PURCHASE_ID, _REVERSE_ADMIN_ID, uow
        )

    uow.commit.assert_not_called()


# ──────────────────────────────────────────────────────────────────────────────
# PurchaseService.confirm_purchase_manually — happy path
# ──────────────────────────────────────────────────────────────────────────────

_CONFIRM_PURCHASE_ID = "bb000001-0000-0000-0000-000000000001"
_CONFIRM_ADMIN_ID = "e9f4b3c2-6b5c-5d4e-7c3b-6a5e4d3c2b2a"
_CONFIRM_USER_ID = "c7e2c1a2-4f3a-4e2b-9c1a-8d2e3f4b5c7d"


@pytest.mark.asyncio
async def test_confirm_purchase_manually_returns_confirmed_purchase_on_success(
    purchase_service: PurchaseService,
    purchase_repository: Mock,
    purchase_factory: Callable[..., Purchase],
) -> None:
    # Arrange
    uow = _make_uow()
    cashback_amount = Decimal("10.00")
    pending_purchase = purchase_factory(
        id=_CONFIRM_PURCHASE_ID,
        user_id=_CONFIRM_USER_ID,
        cashback_amount=cashback_amount,
        status="pending",
    )
    confirmed_purchase = purchase_factory(
        id=_CONFIRM_PURCHASE_ID,
        user_id=_CONFIRM_USER_ID,
        cashback_amount=cashback_amount,
        status="confirmed",
    )
    purchase_repository.get_by_id = AsyncMock(return_value=pending_purchase)
    purchase_repository.update_status = AsyncMock(return_value=confirmed_purchase)
    purchase_service.repository = purchase_repository
    purchase_service.cashback_client.confirm = AsyncMock()
    purchase_service.wallets_client.confirm_pending = AsyncMock()

    # Act
    result = await purchase_service.confirm_purchase_manually(
        _CONFIRM_PURCHASE_ID, _CONFIRM_ADMIN_ID, uow
    )

    # Assert
    assert result.status == "confirmed"
    assert result.cashback_amount == cashback_amount


@pytest.mark.asyncio
async def test_confirm_purchase_manually_commits_uow_on_success(
    purchase_service: PurchaseService,
    purchase_repository: Mock,
    purchase_factory: Callable[..., Purchase],
) -> None:
    # Arrange
    uow = _make_uow()
    pending_purchase = purchase_factory(
        id=_CONFIRM_PURCHASE_ID,
        user_id=_CONFIRM_USER_ID,
        cashback_amount=Decimal("10.00"),
        status="pending",
    )
    confirmed_purchase = purchase_factory(status="confirmed")
    purchase_repository.get_by_id = AsyncMock(return_value=pending_purchase)
    purchase_repository.update_status = AsyncMock(return_value=confirmed_purchase)
    purchase_service.repository = purchase_repository
    purchase_service.cashback_client.confirm = AsyncMock()
    purchase_service.wallets_client.confirm_pending = AsyncMock()

    # Act
    await purchase_service.confirm_purchase_manually(
        _CONFIRM_PURCHASE_ID, _CONFIRM_ADMIN_ID, uow
    )

    # Assert
    uow.commit.assert_called_once()


@pytest.mark.asyncio
async def test_confirm_purchase_manually_publishes_domain_event_on_success(
    purchase_service: PurchaseService,
    purchase_repository: Mock,
    broker: Mock,
    purchase_factory: Callable[..., Purchase],
) -> None:
    # Arrange
    uow = _make_uow()
    cashback_amount = Decimal("10.00")
    pending_purchase = purchase_factory(
        id=_CONFIRM_PURCHASE_ID,
        user_id=_CONFIRM_USER_ID,
        merchant_id="m1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d",
        amount=Decimal("100.00"),
        currency="EUR",
        cashback_amount=cashback_amount,
        status="pending",
    )
    confirmed_purchase = purchase_factory(status="confirmed")
    purchase_repository.get_by_id = AsyncMock(return_value=pending_purchase)
    purchase_repository.update_status = AsyncMock(return_value=confirmed_purchase)
    purchase_service.repository = purchase_repository
    purchase_service.cashback_client.confirm = AsyncMock()
    purchase_service.wallets_client.confirm_pending = AsyncMock()
    purchase_service.broker = broker
    broker.publish = AsyncMock()

    # Act
    await purchase_service.confirm_purchase_manually(
        _CONFIRM_PURCHASE_ID, _CONFIRM_ADMIN_ID, uow
    )

    # Assert
    broker.publish.assert_called_once()
    event = broker.publish.call_args[0][0]
    assert isinstance(event, PurchaseConfirmedByAdmin)
    assert event.purchase_id == _CONFIRM_PURCHASE_ID
    assert event.user_id == _CONFIRM_USER_ID
    assert event.admin_id == _CONFIRM_ADMIN_ID
    assert event.merchant_id == pending_purchase.merchant_id
    assert event.amount == Decimal("100.00")
    assert event.currency == "EUR"
    assert event.cashback_amount == cashback_amount


# ──────────────────────────────────────────────────────────────────────────────
# PurchaseService.confirm_purchase_manually — sad paths
# ──────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_confirm_purchase_manually_raises_on_purchase_not_found(
    purchase_service: PurchaseService,
    purchase_repository: Mock,
) -> None:
    # Arrange
    uow = _make_uow()
    purchase_repository.get_by_id.return_value = None

    # Act & Assert
    with pytest.raises(PurchaseNotFoundException) as exc_info:
        await purchase_service.confirm_purchase_manually(
            _CONFIRM_PURCHASE_ID, _CONFIRM_ADMIN_ID, uow
        )

    assert exc_info.value.purchase_id == _CONFIRM_PURCHASE_ID


@pytest.mark.asyncio
async def test_confirm_purchase_manually_does_not_commit_uow_on_not_found(
    purchase_service: PurchaseService,
    purchase_repository: Mock,
) -> None:
    # Arrange
    uow = _make_uow()
    purchase_repository.get_by_id.return_value = None

    # Act & Assert
    with pytest.raises(PurchaseNotFoundException):
        await purchase_service.confirm_purchase_manually(
            _CONFIRM_PURCHASE_ID, _CONFIRM_ADMIN_ID, uow
        )

    uow.commit.assert_not_called()


@pytest.mark.asyncio
async def test_confirm_purchase_manually_raises_on_not_pending(
    purchase_service: PurchaseService,
    purchase_repository: Mock,
    enforce_purchase_pending: Mock,
    purchase_factory: Callable[..., Purchase],
) -> None:
    # Arrange
    uow = _make_uow()
    confirmed_purchase = purchase_factory(
        id=_CONFIRM_PURCHASE_ID, user_id=_CONFIRM_USER_ID, status="confirmed"
    )
    purchase_repository.get_by_id.return_value = confirmed_purchase
    enforce_purchase_pending.side_effect = PurchaseNotPendingException(
        _CONFIRM_PURCHASE_ID, "confirmed"
    )

    # Act & Assert
    with pytest.raises(PurchaseNotPendingException) as exc_info:
        await purchase_service.confirm_purchase_manually(
            _CONFIRM_PURCHASE_ID, _CONFIRM_ADMIN_ID, uow
        )

    assert exc_info.value.purchase_id == _CONFIRM_PURCHASE_ID
    assert exc_info.value.current_status == "confirmed"


@pytest.mark.asyncio
async def test_confirm_purchase_manually_does_not_commit_uow_on_not_pending(
    purchase_service: PurchaseService,
    purchase_repository: Mock,
    enforce_purchase_pending: Mock,
    purchase_factory: Callable[..., Purchase],
) -> None:
    # Arrange
    uow = _make_uow()
    confirmed_purchase = purchase_factory(
        id=_CONFIRM_PURCHASE_ID, user_id=_CONFIRM_USER_ID, status="confirmed"
    )
    purchase_repository.get_by_id.return_value = confirmed_purchase
    enforce_purchase_pending.side_effect = PurchaseNotPendingException(
        _CONFIRM_PURCHASE_ID, "confirmed"
    )

    # Act & Assert
    with pytest.raises(PurchaseNotPendingException):
        await purchase_service.confirm_purchase_manually(
            _CONFIRM_PURCHASE_ID, _CONFIRM_ADMIN_ID, uow
        )

    uow.commit.assert_not_called()


@pytest.mark.asyncio
async def test_confirm_purchase_manually_calls_apply_helper(
    purchase_service: PurchaseService,
    purchase_repository: Mock,
    purchase_factory: Callable[..., Purchase],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify confirm_purchase_manually calls apply_purchase_confirmation helper."""
    # Arrange
    uow = _make_uow()
    pending_purchase = purchase_factory(
        id=_CONFIRM_PURCHASE_ID,
        user_id=_CONFIRM_USER_ID,
        cashback_amount=Decimal("10.00"),
        status="pending",
    )
    confirmed_purchase = purchase_factory(status="confirmed")
    purchase_repository.get_by_id = AsyncMock(return_value=pending_purchase)
    purchase_service.repository = purchase_repository

    apply_helper_mock = AsyncMock(return_value=confirmed_purchase)
    monkeypatch.setattr(
        "app.purchases.services.apply_purchase_confirmation",
        apply_helper_mock,
    )

    # Act
    await purchase_service.confirm_purchase_manually(
        _CONFIRM_PURCHASE_ID, _CONFIRM_ADMIN_ID, uow
    )

    # Assert
    apply_helper_mock.assert_called_once_with(
        purchase=pending_purchase,
        db=uow.session,
        repository=purchase_repository,
        cashback_client=purchase_service.cashback_client,
        wallets_client=purchase_service.wallets_client,
    )
