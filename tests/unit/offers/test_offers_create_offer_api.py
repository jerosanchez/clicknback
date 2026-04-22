from typing import Any, Callable
from unittest.mock import Mock

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.core.errors.codes import ErrorCode
from app.merchants.exceptions import MerchantNotFoundException
from app.offers.errors import ErrorCode as OfferErrorCode
from app.offers.exceptions import (
    ActiveOfferAlreadyExistsException,
    InvalidCashbackValueException,
    InvalidDateRangeException,
    InvalidMonthlyCapException,
    MerchantNotActiveException,
    PastOfferStartDateException,
)
from app.offers.models import Offer
from tests.unit.offers.conftest import assert_error_code


def _assert_offer_out_response(data: dict[str, Any], offer: Offer) -> None:
    assert data["id"] == str(offer.id)
    assert data["merchant_id"] == str(offer.merchant_id)
    expected_cashback_type = "fixed" if offer.fixed_amount is not None else "percent"
    assert data["cashback_type"] == expected_cashback_type
    expected_cashback_value = (
        offer.fixed_amount if offer.fixed_amount is not None else offer.percentage
    )
    assert data["cashback_value"] == expected_cashback_value
    assert data["status"] == ("active" if offer.active else "inactive")


# ──────────────────────────────────────────────────────────────────────────────
# POST /api/v1/offers
# ──────────────────────────────────────────────────────────────────────────────


def test_create_offer_returns_201_on_success(
    admin_api_client: TestClient,
    offer_service_mock: Mock,
    offer_factory: Callable[..., Offer],
    offer_input_data: Callable[[Offer], dict[str, Any]],
) -> None:
    # Arrange
    offer = offer_factory()
    offer_service_mock.create_offer.return_value = offer
    request_data = offer_input_data(offer)

    # Act
    response = admin_api_client.post("/api/v1/offers", json=request_data)

    # Assert
    assert response.status_code == status.HTTP_201_CREATED
    _assert_offer_out_response(response.json(), offer)


def test_create_offer_enforces_admin_user(
    non_admin_client: TestClient,
    offer_factory: Callable[..., Offer],
    offer_input_data: Callable[[Offer], dict[str, Any]],
) -> None:
    # Act
    response = non_admin_client.post(
        "/api/v1/offers", json=offer_input_data(offer_factory())
    )

    # Assert
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert_error_code(response.json(), ErrorCode.FORBIDDEN)


@pytest.mark.parametrize(
    "exception,expected_status,expected_code",
    [
        (
            InvalidCashbackValueException("percent", 150.0, "Must be <= 100."),
            status.HTTP_400_BAD_REQUEST,
            ErrorCode.VALIDATION_ERROR,
        ),
        (
            PastOfferStartDateException(
                __import__("datetime").date(2025, 1, 1),
            ),
            status.HTTP_400_BAD_REQUEST,
            ErrorCode.VALIDATION_ERROR,
        ),
        (
            InvalidDateRangeException(
                __import__("datetime").date(2026, 12, 31),
                __import__("datetime").date(2026, 6, 1),
            ),
            status.HTTP_400_BAD_REQUEST,
            ErrorCode.VALIDATION_ERROR,
        ),
        (
            InvalidMonthlyCapException(0.0),
            status.HTTP_400_BAD_REQUEST,
            ErrorCode.VALIDATION_ERROR,
        ),
        (
            MerchantNotFoundException("00000000-0000-0000-0000-000000000000"),
            status.HTTP_404_NOT_FOUND,
            ErrorCode.NOT_FOUND,
        ),
        (
            MerchantNotActiveException("a1b2c3d4-e5f6-7890-abcd-ef1234567890"),
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            OfferErrorCode.MERCHANT_NOT_ACTIVE,
        ),
        (
            ActiveOfferAlreadyExistsException("a1b2c3d4-e5f6-7890-abcd-ef1234567890"),
            status.HTTP_409_CONFLICT,
            OfferErrorCode.ACTIVE_OFFER_ALREADY_EXISTS,
        ),
        (
            Exception("Unexpected DB failure"),
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            ErrorCode.INTERNAL_SERVER_ERROR,
        ),
    ],
)
def test_create_offer_returns_error_on_exception(
    admin_api_client: TestClient,
    offer_service_mock: Mock,
    offer_factory: Callable[..., Offer],
    offer_input_data: Callable[[Offer], dict[str, Any]],
    exception: Exception,
    expected_status: int,
    expected_code: str,
) -> None:
    # Arrange
    offer_service_mock.create_offer.side_effect = exception

    # Act
    response = admin_api_client.post(
        "/api/v1/offers", json=offer_input_data(offer_factory())
    )

    # Assert
    assert response.status_code == expected_status
    assert_error_code(response.json(), expected_code)


def test_create_offer_response_maps_all_fields_correctly(
    admin_api_client: TestClient,
    offer_service_mock: Mock,
    offer_factory: Callable[..., Offer],
    offer_input_data: Callable[[Offer], dict[str, Any]],
) -> None:
    """Verify the full ORM→schema field mapping for a non-default offer
    (inactive, percentage-based) to cover all derived fields."""
    # Arrange
    inactive_offer = offer_factory(active=False)
    offer_service_mock.create_offer.return_value = inactive_offer

    # Act
    response = admin_api_client.post(
        "/api/v1/offers", json=offer_input_data(inactive_offer)
    )

    # Assert
    assert response.status_code == status.HTTP_201_CREATED
    _assert_offer_out_response(response.json(), inactive_offer)
