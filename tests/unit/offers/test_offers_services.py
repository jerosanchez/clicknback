from datetime import date
from typing import Any, Callable
from unittest.mock import AsyncMock, Mock, create_autospec

import pytest

from app.merchants.exceptions import MerchantNotFoundException
from app.merchants.models import Merchant
from app.merchants.repository import MerchantRepositoryABC
from app.offers.exceptions import (
    ActiveOfferAlreadyExistsException,
    InactiveMerchantForOfferException,
    InactiveOfferException,
    InvalidCashbackValueException,
    InvalidDateRangeException,
    InvalidMonthlyCapException,
    MerchantNotActiveException,
    OfferNotFoundException,
)
from app.offers.models import Offer
from app.offers.repositories import OfferRepositoryABC
from app.offers.schemas import CashbackTypeEnum
from app.offers.services import OfferService


@pytest.fixture
def enforce_cashback_value_validity_mock() -> Mock:
    return Mock()


@pytest.fixture
def enforce_date_range_validity_mock() -> Mock:
    return Mock()


@pytest.fixture
def enforce_monthly_cap_validity_mock() -> Mock:
    return Mock()


@pytest.fixture
def enforce_merchant_is_active_mock() -> Mock:
    return Mock()


@pytest.fixture
def enforce_no_active_offer_exists_mock() -> Mock:
    return Mock()


@pytest.fixture
def enforce_offer_visibility_mock() -> Mock:
    return Mock()


@pytest.fixture
def enforce_offer_merchant_visibility_mock() -> Mock:
    return Mock()


@pytest.fixture
def offer_repository_mock() -> Mock:
    return create_autospec(OfferRepositoryABC)


@pytest.fixture
def merchant_repository_mock() -> Mock:
    return create_autospec(MerchantRepositoryABC)


@pytest.fixture
def offer_service(
    enforce_cashback_value_validity_mock: Mock,
    enforce_date_range_validity_mock: Mock,
    enforce_monthly_cap_validity_mock: Mock,
    enforce_merchant_is_active_mock: Mock,
    enforce_no_active_offer_exists_mock: Mock,
    enforce_offer_visibility_mock: Mock,
    enforce_offer_merchant_visibility_mock: Mock,
    offer_repository_mock: Mock,
    merchant_repository_mock: Mock,
) -> OfferService:
    return OfferService(
        enforce_cashback_value_validity=enforce_cashback_value_validity_mock,
        enforce_date_range_validity=enforce_date_range_validity_mock,
        enforce_monthly_cap_validity=enforce_monthly_cap_validity_mock,
        enforce_merchant_is_active=enforce_merchant_is_active_mock,
        enforce_no_active_offer_exists=enforce_no_active_offer_exists_mock,
        enforce_offer_visibility=enforce_offer_visibility_mock,
        enforce_offer_merchant_visibility=enforce_offer_merchant_visibility_mock,
        offer_repository=offer_repository_mock,
        merchant_repository=merchant_repository_mock,
    )


def _make_offer_create(**overrides: Any) -> dict[str, Any]:
    defaults: dict[str, Any] = {
        "merchant_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
        "cashback_type": CashbackTypeEnum.percent,
        "cashback_value": 10.0,
        "start_date": date(2026, 3, 1),
        "end_date": date(2026, 12, 31),
        "monthly_cap": 50.0,
    }
    defaults.update(overrides)
    return defaults


def _make_uow() -> Mock:
    """Create a fresh mock UnitOfWork for write service tests."""
    uow = Mock()
    uow.session = AsyncMock()
    uow.commit = AsyncMock()
    uow.rollback = AsyncMock()
    return uow


# ──────────────────────────────────────────────────────────────────────────────
# OfferService.create_offer
# ──────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_offer_returns_offer_on_success(
    offer_service: OfferService,
    offer_repository_mock: Mock,
    merchant_repository_mock: Mock,
    offer_factory: Callable[..., Offer],
    merchant_factory: Callable[..., Merchant],
) -> None:
    # Arrange
    uow = _make_uow()
    data = _make_offer_create()
    merchant = merchant_factory(active=True)
    expected_offer = offer_factory()
    merchant_repository_mock.get_merchant_by_id.return_value = merchant
    offer_repository_mock.has_active_offer_for_merchant.return_value = False
    offer_repository_mock.add_offer.return_value = expected_offer

    # Act
    result = await offer_service.create_offer(data, uow)

    # Assert
    assert result == expected_offer
    uow.commit.assert_called_once()


@pytest.mark.asyncio
async def test_create_offer_enforces_cashback_value_validity_policy(
    offer_service: OfferService,
    enforce_cashback_value_validity_mock: Mock,
) -> None:
    # Arrange
    uow = _make_uow()
    data = _make_offer_create()
    enforce_cashback_value_validity_mock.side_effect = InvalidCashbackValueException(
        "percent", 150.0, "Must be between 0 and 20."
    )

    # Act & Assert
    with pytest.raises(InvalidCashbackValueException):
        await offer_service.create_offer(data, uow)

    uow.commit.assert_not_called()


@pytest.mark.asyncio
async def test_create_offer_enforces_date_range_validity_policy(
    offer_service: OfferService,
    enforce_date_range_validity_mock: Mock,
) -> None:
    # Arrange
    uow = _make_uow()
    data = _make_offer_create()
    enforce_date_range_validity_mock.side_effect = InvalidDateRangeException(
        date(2026, 12, 31), date(2026, 1, 1)
    )

    # Act & Assert
    with pytest.raises(InvalidDateRangeException):
        await offer_service.create_offer(data, uow)

    uow.commit.assert_not_called()


@pytest.mark.asyncio
async def test_create_offer_enforces_monthly_cap_validity_policy(
    offer_service: OfferService,
    enforce_monthly_cap_validity_mock: Mock,
) -> None:
    # Arrange
    uow = _make_uow()
    data = _make_offer_create()
    enforce_monthly_cap_validity_mock.side_effect = InvalidMonthlyCapException(0.0)

    # Act & Assert
    with pytest.raises(InvalidMonthlyCapException):
        await offer_service.create_offer(data, uow)

    uow.commit.assert_not_called()


@pytest.mark.asyncio
async def test_create_offer_raises_on_merchant_not_found(
    offer_service: OfferService,
    merchant_repository_mock: Mock,
) -> None:
    # Arrange
    uow = _make_uow()
    data = _make_offer_create()
    merchant_repository_mock.get_merchant_by_id.return_value = None

    # Act & Assert
    with pytest.raises(MerchantNotFoundException):
        await offer_service.create_offer(data, uow)

    uow.commit.assert_not_called()


@pytest.mark.asyncio
async def test_create_offer_enforces_merchant_is_active_policy(
    offer_service: OfferService,
    merchant_repository_mock: Mock,
    enforce_merchant_is_active_mock: Mock,
    merchant_factory: Callable[..., Merchant],
) -> None:
    # Arrange
    uow = _make_uow()
    data = _make_offer_create()
    inactive_merchant = merchant_factory(active=False)
    merchant_repository_mock.get_merchant_by_id.return_value = inactive_merchant
    enforce_merchant_is_active_mock.side_effect = MerchantNotActiveException(
        str(data["merchant_id"])
    )

    # Act & Assert
    with pytest.raises(MerchantNotActiveException):
        await offer_service.create_offer(data, uow)

    uow.commit.assert_not_called()


@pytest.mark.asyncio
async def test_create_offer_enforces_no_active_offer_exists_policy(
    offer_service: OfferService,
    merchant_repository_mock: Mock,
    offer_repository_mock: Mock,
    enforce_no_active_offer_exists_mock: Mock,
    merchant_factory: Callable[..., Merchant],
) -> None:
    # Arrange
    uow = _make_uow()
    data = _make_offer_create()
    active_merchant = merchant_factory(active=True)
    merchant_repository_mock.get_merchant_by_id.return_value = active_merchant
    offer_repository_mock.has_active_offer_for_merchant.return_value = True
    enforce_no_active_offer_exists_mock.side_effect = ActiveOfferAlreadyExistsException(
        str(data["merchant_id"])
    )

    # Act & Assert
    with pytest.raises(ActiveOfferAlreadyExistsException):
        await offer_service.create_offer(data, uow)

    uow.commit.assert_not_called()


@pytest.mark.asyncio
async def test_create_offer_maps_percent_type_correctly(
    offer_service: OfferService,
    offer_repository_mock: Mock,
    merchant_repository_mock: Mock,
    offer_factory: Callable[..., Offer],
    merchant_factory: Callable[..., Merchant],
) -> None:
    """Verify that a percent offer maps cashback_value → percentage and
    sets fixed_amount to None on the persisted Offer."""
    # Arrange
    uow = _make_uow()
    percent_value = 15.0
    data = _make_offer_create(
        cashback_type=CashbackTypeEnum.percent, cashback_value=percent_value
    )
    merchant_repository_mock.get_merchant_by_id.return_value = merchant_factory()
    offer_repository_mock.has_active_offer_for_merchant.return_value = False
    offer_repository_mock.add_offer.side_effect = lambda _db, o: o  # type: ignore

    # Act
    result = await offer_service.create_offer(data, uow)

    # Assert
    assert result.percentage == percent_value
    assert result.fixed_amount is None


@pytest.mark.asyncio
async def test_create_offer_maps_fixed_type_correctly(
    offer_service: OfferService,
    offer_repository_mock: Mock,
    merchant_repository_mock: Mock,
    merchant_factory: Callable[..., Merchant],
) -> None:
    """Verify that a fixed offer maps cashback_value → fixed_amount and
    sets percentage to 0 on the persisted Offer."""
    # Arrange
    uow = _make_uow()
    fixed_value = 5.0
    data = _make_offer_create(
        cashback_type=CashbackTypeEnum.fixed, cashback_value=fixed_value
    )
    merchant_repository_mock.get_merchant_by_id.return_value = merchant_factory()
    offer_repository_mock.has_active_offer_for_merchant.return_value = False
    offer_repository_mock.add_offer.side_effect = lambda _db, o: o  # type: ignore

    # Act
    result = await offer_service.create_offer(data, uow)

    # Assert
    assert result.fixed_amount == fixed_value
    assert result.percentage == 0.0


# ──────────────────────────────────────────────────────────────────────────────
# OfferService.list_offers
# ──────────────────────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "num_items,expected_total,active_filter",
    [
        (3, 3, None),  # multiple items, no filter
        (0, 0, None),  # empty result, no filter
        (1, 1, True),  # active filter applied
        (2, 2, False),  # inactive filter applied
    ],
)
@pytest.mark.asyncio
async def test_list_offers_returns_repository_result_on_call(
    offer_service: OfferService,
    offer_repository_mock: Mock,
    offer_factory: Callable[..., Offer],
    num_items: int,
    expected_total: int,
    active_filter: bool | None,
) -> None:
    # Arrange
    db = AsyncMock()
    offers = [
        offer_factory(id=f"f0e1d2c3-b4a5-4678-{i:04d}-3456789abcde")
        for i in range(num_items)
    ]
    offer_repository_mock.list_offers.return_value = (offers, expected_total)

    # Act
    items, total = await offer_service.list_offers(
        offset=0,
        limit=20,
        active=active_filter,
        merchant_id=None,
        date_from=None,
        date_to=None,
        db=db,
    )

    # Assert
    assert items == offers
    assert total == expected_total
    offer_repository_mock.list_offers.assert_called_once_with(
        db, 0, 20, active=active_filter, merchant_id=None, date_from=None, date_to=None
    )


# ──────────────────────────────────────────────────────────────────────────────
# OfferService.list_active_offers
# ──────────────────────────────────────────────────────────────────────────────

# It is a simple forwarding method to the repository, no tests required.


# ──────────────────────────────────────────────────────────────────────────────
# OfferService.set_offer_status
# ──────────────────────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "target_active",
    [True, False],
    ids=["activate", "deactivate"],
)
@pytest.mark.asyncio
async def test_set_offer_status_returns_updated_offer(
    offer_service: OfferService,
    offer_repository_mock: Mock,
    offer_factory: Callable[..., Offer],
    target_active: bool,
) -> None:
    # Arrange
    uow = _make_uow()
    existing = offer_factory(active=not target_active)
    updated = offer_factory(active=target_active)
    offer_repository_mock.get_offer_by_id.return_value = existing
    offer_repository_mock.update_offer_status.return_value = updated

    # Act
    result = await offer_service.set_offer_status(existing.id, target_active, uow)

    # Assert
    assert result == updated
    uow.commit.assert_called_once()


@pytest.mark.asyncio
async def test_set_offer_status_raises_on_offer_not_found(
    offer_service: OfferService,
    offer_repository_mock: Mock,
) -> None:
    # Arrange
    uow = _make_uow()
    missing_offer_id = "00000000-0000-0000-0000-000000000000"
    offer_repository_mock.get_offer_by_id.return_value = None

    # Act & Assert
    with pytest.raises(OfferNotFoundException) as exc_info:
        await offer_service.set_offer_status(missing_offer_id, True, uow)

    assert exc_info.value.offer_id == missing_offer_id
    uow.commit.assert_not_called()


# ──────────────────────────────────────────────────────────────────────────────
# OfferService.get_offer_details
# ──────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_offer_details_returns_offer_and_merchant_name_on_success(
    offer_service: OfferService,
    offer_repository_mock: Mock,
    offer_factory: Callable[..., Offer],
) -> None:
    # Arrange
    db = AsyncMock()
    offer = offer_factory(active=True)
    merchant_name = "Shoply"
    merchant_active = True
    offer_repository_mock.get_offer_with_merchant_name.return_value = (
        offer,
        merchant_name,
        merchant_active,
    )

    # Act
    result_offer, result_merchant_name = await offer_service.get_offer_details(
        offer.id, is_admin=False, db=db
    )

    # Assert
    assert result_offer == offer
    assert result_merchant_name == merchant_name


@pytest.mark.asyncio
async def test_get_offer_details_raises_on_offer_not_found(
    offer_service: OfferService,
    offer_repository_mock: Mock,
) -> None:
    # Arrange
    db = AsyncMock()
    missing_offer_id = "00000000-0000-0000-0000-000000000000"
    offer_repository_mock.get_offer_with_merchant_name.return_value = None

    # Act & Assert
    with pytest.raises(OfferNotFoundException) as exc_info:
        await offer_service.get_offer_details(missing_offer_id, is_admin=False, db=db)

    assert exc_info.value.offer_id == missing_offer_id


@pytest.mark.asyncio
async def test_get_offer_details_enforces_offer_visibility_policy(
    offer_service: OfferService,
    offer_repository_mock: Mock,
    enforce_offer_visibility_mock: Mock,
    offer_factory: Callable[..., Offer],
) -> None:
    # Arrange
    db = AsyncMock()
    inactive_offer = offer_factory(active=False)
    offer_repository_mock.get_offer_with_merchant_name.return_value = (
        inactive_offer,
        "Shoply",
        True,
    )
    enforce_offer_visibility_mock.side_effect = InactiveOfferException(
        inactive_offer.id
    )

    # Act & Assert
    with pytest.raises(InactiveOfferException):
        await offer_service.get_offer_details(inactive_offer.id, is_admin=False, db=db)


@pytest.mark.asyncio
async def test_get_offer_details_enforces_offer_merchant_visibility_policy(
    offer_service: OfferService,
    offer_repository_mock: Mock,
    enforce_offer_merchant_visibility_mock: Mock,
    offer_factory: Callable[..., Offer],
) -> None:
    # Arrange
    db = AsyncMock()
    offer = offer_factory(active=True)
    inactive_merchant_name = "LuxWatches"
    inactive_merchant_active = False
    offer_repository_mock.get_offer_with_merchant_name.return_value = (
        offer,
        inactive_merchant_name,
        inactive_merchant_active,
    )
    enforce_offer_merchant_visibility_mock.side_effect = (
        InactiveMerchantForOfferException(offer.id, offer.merchant_id)
    )

    # Act & Assert
    with pytest.raises(InactiveMerchantForOfferException):
        await offer_service.get_offer_details(offer.id, is_admin=False, db=db)


@pytest.mark.asyncio
async def test_get_offer_details_admin_calls_policies_with_is_admin_true(
    offer_service: OfferService,
    offer_repository_mock: Mock,
    enforce_offer_visibility_mock: Mock,
    enforce_offer_merchant_visibility_mock: Mock,
    offer_factory: Callable[..., Offer],
) -> None:
    # Arrange
    db = AsyncMock()
    inactive_offer = offer_factory(active=False)
    inactive_merchant_active = False
    offer_repository_mock.get_offer_with_merchant_name.return_value = (
        inactive_offer,
        "LuxWatches",
        inactive_merchant_active,
    )
    # Policies do NOT raise (mock default) — admin bypass is implemented inside policies

    # Act
    result_offer, result_merchant_name = await offer_service.get_offer_details(
        inactive_offer.id, is_admin=True, db=db
    )

    # Assert
    enforce_offer_visibility_mock.assert_called_once_with(
        inactive_offer.id, inactive_offer.active, True
    )
    enforce_offer_merchant_visibility_mock.assert_called_once_with(
        inactive_offer.id,
        str(inactive_offer.merchant_id),
        inactive_merchant_active,
        True,
    )
    assert result_offer == inactive_offer
    assert result_merchant_name == "LuxWatches"
