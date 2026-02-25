from typing import Any, Callable
from unittest.mock import Mock, create_autospec

import pytest
from sqlalchemy.orm import Session

from app.merchants.exceptions import (
    CashbackPercentageNotValidException,
    MerchantNameAlreadyExistsException,
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


def test_create_merchant_success(
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


def test_create_merchant_raises_exception_on_name_already_exists(
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


def test_create_merchant_propagates_exception_on_invalid_cashback_percentage(
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
