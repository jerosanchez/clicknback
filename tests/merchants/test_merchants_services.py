from typing import Any, Callable
from unittest.mock import Mock, create_autospec

import pytest
from sqlalchemy.orm import Session

from app.merchants.exceptions import (
    CashbackPercentageNotValidException,
    MerchantNameAlreadyExistsException,
    MerchantNotFoundException,
)
from app.merchants.models import Merchant
from app.merchants.repository import MerchantRepositoryABC
from app.merchants.services import MerchantService


@pytest.fixture
def enforce_cashback_percentage_validity() -> Callable[[float], None]:
    return Mock()


@pytest.fixture
def merchant_repository() -> Mock:
    return create_autospec(MerchantRepositoryABC)


@pytest.fixture
def merchant_service(
    enforce_cashback_percentage_validity: Callable[[float], None],
    merchant_repository: Mock,
) -> MerchantService:
    return MerchantService(
        enforce_cashback_percentage_validity=enforce_cashback_percentage_validity,
        merchant_repository=merchant_repository,
    )


# ──────────────────────────────────────────────────────────────────────────────
# MerchantService.create_merchant
# ──────────────────────────────────────────────────────────────────────────────


def test_create_merchant_returns_merchant_on_success(
    merchant_service: MerchantService,
    merchant_repository: Mock,
    merchant_factory: Callable[..., Merchant],
    merchant_input_data: Callable[[Merchant], dict[str, Any]],
) -> None:
    # Arrange
    db = Mock(spec=Session)
    new_merchant = merchant_factory()
    merchant_repository.get_merchant_by_name.return_value = None
    merchant_repository.add_merchant.return_value = new_merchant
    data = merchant_input_data(new_merchant)

    # Act
    returned_merchant = merchant_service.create_merchant(data, db)

    # Assert
    assert returned_merchant == new_merchant


def test_create_merchant_raises_on_name_already_exists(
    merchant_service: MerchantService,
    merchant_repository: Mock,
    merchant_factory: Callable[..., Merchant],
    merchant_input_data: Callable[[Merchant], dict[str, Any]],
) -> None:
    # Arrange
    db = Mock(spec=Session)
    existing_merchant = merchant_factory()
    merchant_repository.get_merchant_by_name.return_value = existing_merchant
    data = merchant_input_data(existing_merchant)

    # Act & Assert
    with pytest.raises(MerchantNameAlreadyExistsException):
        merchant_service.create_merchant(data, db)


def test_create_merchant_raises_on_invalid_cashback_percentage(
    merchant_service: MerchantService,
    enforce_cashback_percentage_validity: Mock,
    merchant_repository: Mock,
    merchant_factory: Callable[..., Merchant],
    merchant_input_data: Callable[[Merchant], dict[str, Any]],
) -> None:
    # Arrange
    db = Mock(spec=Session)
    merchant = merchant_factory()
    merchant_repository.get_merchant_by_name.return_value = None
    enforce_cashback_percentage_validity.side_effect = (
        CashbackPercentageNotValidException("must be between 0 and 20.")
    )
    data = merchant_input_data(merchant)

    # Act & Assert
    with pytest.raises(CashbackPercentageNotValidException):
        merchant_service.create_merchant(data, db)


# ──────────────────────────────────────────────────────────────────────────────
# MerchantService.list_merchants
# ──────────────────────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "num_items,expected_total,active_filter",
    [
        (3, 3, None),  # multiple items, no filter
        (0, 0, None),  # empty result, no filter
        (1, 1, True),  # active filter applied
    ],
)
def test_list_merchants_returns_repository_result_on_call(
    merchant_service: MerchantService,
    merchant_repository: Mock,
    merchant_factory: Callable[..., Merchant],
    num_items: int,
    expected_total: int,
    active_filter: bool | None,
) -> None:
    # Arrange
    db = Mock(spec=Session)
    merchants = [merchant_factory(name=f"Merchant {i}") for i in range(num_items)]
    merchant_repository.list_merchants.return_value = (merchants, expected_total)

    # Act
    items, total = merchant_service.list_merchants(
        page=1, page_size=20, active=active_filter, db=db
    )

    # Assert
    assert items == merchants
    assert total == expected_total
    merchant_repository.list_merchants.assert_called_once_with(db, 1, 20, active_filter)


# ──────────────────────────────────────────────────────────────────────────────
# MerchantService.set_merchant_status
# ──────────────────────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "target_active",
    [True, False],
    ids=["activate", "deactivate"],
)
def test_set_merchant_status_returns_updated_merchant(
    merchant_service: MerchantService,
    merchant_repository: Mock,
    merchant_factory: Callable[..., Merchant],
    target_active: bool,
) -> None:
    # Arrange
    db = Mock(spec=Session)
    existing = merchant_factory(active=not target_active)
    updated = merchant_factory(active=target_active)
    merchant_repository.get_merchant_by_id.return_value = existing
    merchant_repository.update_merchant_status.return_value = updated

    # Act
    result = merchant_service.set_merchant_status(existing.id, target_active, db)

    # Assert
    assert result == updated
    merchant_repository.update_merchant_status.assert_called_once_with(
        db, existing, target_active
    )


def test_set_merchant_status_raises_on_merchant_not_found(
    merchant_service: MerchantService,
    merchant_repository: Mock,
) -> None:
    # Arrange
    db = Mock(spec=Session)
    merchant_repository.get_merchant_by_id.return_value = None

    # Act & Assert
    with pytest.raises(MerchantNotFoundException):
        merchant_service.set_merchant_status("nonexistent-id", True, db)
