from typing import Any, Callable
from unittest.mock import Mock

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.core.errors.codes import ErrorCode
from app.offers.exceptions import (
    InactiveMerchantForOfferException,
    InactiveOfferException,
    OfferNotFoundException,
)
from app.offers.models import Offer
from tests.unit.offers.conftest import assert_error_code

_ACTIVE_OFFER_ID = "f0e1d2c3-b4a5-4678-9012-3456789abcde"
_MISSING_OFFER_ID = "00000000-0000-0000-0000-000000000000"


def _assert_offer_details_response(
    data: dict[str, Any], offer: Offer, merchant_name: str
) -> None:
    assert data["id"] == str(offer.id)
    assert data["merchant_name"] == merchant_name
    expected_cashback_type = "fixed" if offer.fixed_amount is not None else "percent"
    assert data["cashback_type"] == expected_cashback_type
    expected_cashback_value = (
        offer.fixed_amount if offer.fixed_amount is not None else offer.percentage
    )
    assert data["cashback_value"] == expected_cashback_value
    assert data["monthly_cap"] == offer.monthly_cap_per_user
    assert data["start_date"] == offer.start_date.isoformat()
    assert data["end_date"] == offer.end_date.isoformat()
    assert data["status"] == ("active" if offer.active else "inactive")


# ──────────────────────────────────────────────────────────────────────────────
# GET /api/v1/offers/{offer_id}
# ──────────────────────────────────────────────────────────────────────────────


def test_get_offer_details_returns_200_on_success(
    user_client: TestClient,
    offer_service_mock: Mock,
    offer_factory: Callable[..., Offer],
) -> None:
    # Arrange
    offer = offer_factory(id=_ACTIVE_OFFER_ID, active=True)
    merchant_name = "Shoply"
    offer_service_mock.get_offer_details.return_value = (offer, merchant_name)

    # Act
    response = user_client.get(f"/api/v1/offers/{_ACTIVE_OFFER_ID}")

    # Assert
    assert response.status_code == status.HTTP_200_OK
    _assert_offer_details_response(response.json(), offer, merchant_name)


def test_get_offer_details_maps_fixed_cashback_correctly(
    user_client: TestClient,
    offer_service_mock: Mock,
    offer_factory: Callable[..., Offer],
) -> None:
    # Arrange
    fixed_offer = offer_factory(
        id=_ACTIVE_OFFER_ID, percentage=0.0, fixed_amount=5.0, active=True
    )
    merchant_name = "QuickCart"
    offer_service_mock.get_offer_details.return_value = (fixed_offer, merchant_name)

    # Act
    response = user_client.get(f"/api/v1/offers/{_ACTIVE_OFFER_ID}")

    # Assert
    assert response.status_code == status.HTTP_200_OK
    _assert_offer_details_response(response.json(), fixed_offer, merchant_name)


def test_get_offer_details_admin_returns_200_on_inactive_offer(
    admin_user_client: TestClient,
    offer_service_mock: Mock,
    offer_factory: Callable[..., Offer],
) -> None:
    # Arrange
    inactive_offer = offer_factory(id=_ACTIVE_OFFER_ID, active=False)
    merchant_name = "UrbanMart"
    offer_service_mock.get_offer_details.return_value = (inactive_offer, merchant_name)

    # Act
    response = admin_user_client.get(f"/api/v1/offers/{_ACTIVE_OFFER_ID}")

    # Assert
    assert response.status_code == status.HTTP_200_OK
    _assert_offer_details_response(response.json(), inactive_offer, merchant_name)


def test_get_offer_details_returns_401_on_unauthenticated_request(
    unauthenticated_client: TestClient,
) -> None:
    # Act
    response = unauthenticated_client.get(f"/api/v1/offers/{_ACTIVE_OFFER_ID}")

    # Assert
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert_error_code(response.json(), ErrorCode.INVALID_TOKEN)


def test_get_offer_details_returns_404_on_offer_not_found(
    user_client: TestClient,
    offer_service_mock: Mock,
) -> None:
    # Arrange
    offer_service_mock.get_offer_details.side_effect = OfferNotFoundException(
        _MISSING_OFFER_ID
    )

    # Act
    response = user_client.get(f"/api/v1/offers/{_MISSING_OFFER_ID}")

    # Assert
    assert response.status_code == status.HTTP_404_NOT_FOUND
    data = response.json()
    assert_error_code(data, ErrorCode.NOT_FOUND)
    assert data["error"]["details"]["resource_type"] == "offer"
    assert data["error"]["details"]["resource_id"] == _MISSING_OFFER_ID


def test_get_offer_details_returns_403_on_inactive_offer_for_non_admin(
    user_client: TestClient,
    offer_service_mock: Mock,
) -> None:
    # Arrange
    inactive_offer_id = "b2c3d4e5-f6a7-4890-abcd-ef1234567890"
    offer_service_mock.get_offer_details.side_effect = InactiveOfferException(
        inactive_offer_id
    )

    # Act
    response = user_client.get(f"/api/v1/offers/{inactive_offer_id}")

    # Assert
    assert response.status_code == status.HTTP_403_FORBIDDEN
    data = response.json()
    assert_error_code(data, ErrorCode.FORBIDDEN)
    assert data["error"]["details"]["resource_type"] == "offer"
    assert data["error"]["details"]["resource_id"] == inactive_offer_id


def test_get_offer_details_returns_403_on_inactive_merchant_for_non_admin(
    user_client: TestClient,
    offer_service_mock: Mock,
) -> None:
    # Arrange
    offer_id = "d0000001-0000-0000-0000-000000000001"
    merchant_id = "a5b6c7d8-e9f0-4a1b-2c3d-4e5f6a7b8c9d"
    offer_service_mock.get_offer_details.side_effect = (
        InactiveMerchantForOfferException(offer_id, merchant_id)
    )

    # Act
    response = user_client.get(f"/api/v1/offers/{offer_id}")

    # Assert
    assert response.status_code == status.HTTP_403_FORBIDDEN
    data = response.json()
    assert_error_code(data, ErrorCode.FORBIDDEN)
    assert data["error"]["details"]["resource_type"] == "offer"
    assert data["error"]["details"]["resource_id"] == offer_id


def test_get_offer_details_returns_500_on_unexpected_error(
    user_client: TestClient,
    offer_service_mock: Mock,
) -> None:
    # Arrange
    offer_service_mock.get_offer_details.side_effect = Exception("DB connection lost")

    # Act
    response = user_client.get(f"/api/v1/offers/{_ACTIVE_OFFER_ID}")

    # Assert
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert_error_code(response.json(), ErrorCode.INTERNAL_SERVER_ERROR)
