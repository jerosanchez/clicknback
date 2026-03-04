from datetime import date
from typing import Any, Callable
from unittest.mock import Mock, create_autospec

import pytest
from sqlalchemy.orm import Session

from app.merchants.exceptions import MerchantNotFoundException
from app.merchants.models import Merchant
from app.merchants.repository import MerchantRepositoryABC
from app.offers.exceptions import (
    ActiveOfferAlreadyExistsException,
    InvalidCashbackValueException,
    InvalidDateRangeException,
    InvalidMonthlyCapException,
    MerchantNotActiveException,
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
    offer_repository_mock: Mock,
    merchant_repository_mock: Mock,
) -> OfferService:
    return OfferService(
        enforce_cashback_value_validity=enforce_cashback_value_validity_mock,
        enforce_date_range_validity=enforce_date_range_validity_mock,
        enforce_monthly_cap_validity=enforce_monthly_cap_validity_mock,
        enforce_merchant_is_active=enforce_merchant_is_active_mock,
        enforce_no_active_offer_exists=enforce_no_active_offer_exists_mock,
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


# ──────────────────────────────────────────────────────────────────────────────
# OfferService.create_offer
# ──────────────────────────────────────────────────────────────────────────────


def test_create_offer_returns_offer_on_success(
    offer_service: OfferService,
    offer_repository_mock: Mock,
    merchant_repository_mock: Mock,
    offer_factory: Callable[..., Offer],
    merchant_factory: Callable[..., Merchant],
) -> None:
    # Arrange
    db = Mock(spec=Session)
    data = _make_offer_create()
    merchant = merchant_factory(active=True)
    expected_offer = offer_factory()
    merchant_repository_mock.get_merchant_by_id.return_value = merchant
    offer_repository_mock.has_active_offer_for_merchant.return_value = False
    offer_repository_mock.add_offer.return_value = expected_offer

    # Act
    result = offer_service.create_offer(data, db)

    # Assert
    assert result == expected_offer


def test_create_offer_enforces_cashback_value_validity_policy(
    offer_service: OfferService,
    enforce_cashback_value_validity_mock: Mock,
) -> None:
    # Arrange
    db = Mock(spec=Session)
    data = _make_offer_create()
    enforce_cashback_value_validity_mock.side_effect = InvalidCashbackValueException(
        "percent", 150.0, "Must be between 0 and 20."
    )

    # Act & Assert
    with pytest.raises(InvalidCashbackValueException):
        offer_service.create_offer(data, db)


def test_create_offer_enforces_date_range_validity_policy(
    offer_service: OfferService,
    enforce_date_range_validity_mock: Mock,
) -> None:
    # Arrange
    db = Mock(spec=Session)
    data = _make_offer_create()
    enforce_date_range_validity_mock.side_effect = InvalidDateRangeException(
        date(2026, 12, 31), date(2026, 1, 1)
    )

    # Act & Assert
    with pytest.raises(InvalidDateRangeException):
        offer_service.create_offer(data, db)


def test_create_offer_enforces_monthly_cap_validity_policy(
    offer_service: OfferService,
    enforce_monthly_cap_validity_mock: Mock,
) -> None:
    # Arrange
    db = Mock(spec=Session)
    data = _make_offer_create()
    enforce_monthly_cap_validity_mock.side_effect = InvalidMonthlyCapException(0.0)

    # Act & Assert
    with pytest.raises(InvalidMonthlyCapException):
        offer_service.create_offer(data, db)


def test_create_offer_raises_on_merchant_not_found(
    offer_service: OfferService,
    merchant_repository_mock: Mock,
) -> None:
    # Arrange
    db = Mock(spec=Session)
    data = _make_offer_create()
    merchant_repository_mock.get_merchant_by_id.return_value = None

    # Act & Assert
    with pytest.raises(MerchantNotFoundException):
        offer_service.create_offer(data, db)


def test_create_offer_enforces_merchant_is_active_policy(
    offer_service: OfferService,
    merchant_repository_mock: Mock,
    enforce_merchant_is_active_mock: Mock,
    merchant_factory: Callable[..., Merchant],
) -> None:
    # Arrange
    db = Mock(spec=Session)
    data = _make_offer_create()
    inactive_merchant = merchant_factory(active=False)
    merchant_repository_mock.get_merchant_by_id.return_value = inactive_merchant
    enforce_merchant_is_active_mock.side_effect = MerchantNotActiveException(
        str(data["merchant_id"])
    )

    # Act & Assert
    with pytest.raises(MerchantNotActiveException):
        offer_service.create_offer(data, db)


def test_create_offer_enforces_no_active_offer_exists_policy(
    offer_service: OfferService,
    merchant_repository_mock: Mock,
    offer_repository_mock: Mock,
    enforce_no_active_offer_exists_mock: Mock,
    merchant_factory: Callable[..., Merchant],
) -> None:
    # Arrange
    db = Mock(spec=Session)
    data = _make_offer_create()
    active_merchant = merchant_factory(active=True)
    merchant_repository_mock.get_merchant_by_id.return_value = active_merchant
    offer_repository_mock.has_active_offer_for_merchant.return_value = True
    enforce_no_active_offer_exists_mock.side_effect = ActiveOfferAlreadyExistsException(
        str(data["merchant_id"])
    )

    # Act & Assert
    with pytest.raises(ActiveOfferAlreadyExistsException):
        offer_service.create_offer(data, db)


def test_create_offer_maps_percent_type_correctly(
    offer_service: OfferService,
    offer_repository_mock: Mock,
    merchant_repository_mock: Mock,
    offer_factory: Callable[..., Offer],
    merchant_factory: Callable[..., Merchant],
) -> None:
    """Verify that a percent offer maps cashback_value → percentage and
    sets fixed_amount to None on the persisted Offer."""
    # Arrange
    db = Mock(spec=Session)
    percent_value = 15.0
    data = _make_offer_create(
        cashback_type=CashbackTypeEnum.percent, cashback_value=percent_value
    )
    merchant_repository_mock.get_merchant_by_id.return_value = merchant_factory()
    offer_repository_mock.has_active_offer_for_merchant.return_value = False
    offer_repository_mock.add_offer.side_effect = lambda _db, o: o  # type: ignore

    # Act
    result = offer_service.create_offer(data, db)

    # Assert
    assert result.percentage == percent_value
    assert result.fixed_amount is None


def test_create_offer_maps_fixed_type_correctly(
    offer_service: OfferService,
    offer_repository_mock: Mock,
    merchant_repository_mock: Mock,
    merchant_factory: Callable[..., Merchant],
) -> None:
    """Verify that a fixed offer maps cashback_value → fixed_amount and
    sets percentage to 0 on the persisted Offer."""
    # Arrange
    db = Mock(spec=Session)
    fixed_value = 5.0
    data = _make_offer_create(
        cashback_type=CashbackTypeEnum.fixed, cashback_value=fixed_value
    )
    merchant_repository_mock.get_merchant_by_id.return_value = merchant_factory()
    offer_repository_mock.has_active_offer_for_merchant.return_value = False
    offer_repository_mock.add_offer.side_effect = lambda _db, o: o  # type: ignore

    # Act
    result = offer_service.create_offer(data, db)

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
def test_list_offers_returns_repository_result_on_call(
    offer_service: OfferService,
    offer_repository_mock: Mock,
    offer_factory: Callable[..., Offer],
    num_items: int,
    expected_total: int,
    active_filter: bool | None,
) -> None:
    # Arrange
    db = Mock(spec=Session)
    offers = [
        offer_factory(id=f"f0e1d2c3-b4a5-4678-{i:04d}-3456789abcde")
        for i in range(num_items)
    ]
    offer_repository_mock.list_offers.return_value = (offers, expected_total)

    # Act
    items, total = offer_service.list_offers(
        page=1,
        page_size=20,
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
        db, 1, 20, active=active_filter, merchant_id=None, date_from=None, date_to=None
    )


# ──────────────────────────────────────────────────────────────────────────────
# OfferService.list_active_offers
# ──────────────────────────────────────────────────────────────────────────────

# It is a simple forwarding method to the repository, no tests required.
