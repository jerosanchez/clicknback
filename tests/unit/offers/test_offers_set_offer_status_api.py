from typing import Any, Callable
from unittest.mock import Mock

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.core.errors.codes import ErrorCode
from app.offers.exceptions import OfferNotFoundException
from app.offers.models import Offer
from tests.unit.offers.conftest import assert_error_code


def _assert_offer_status_response(
    data: dict[str, Any], offer: Offer, expected_status_str: str
) -> None:
    assert data["id"] == str(offer.id)
    assert data["status"] == expected_status_str


# ──────────────────────────────────────────────────────────────────────────────
# PATCH /api/v1/offers/{offer_id}/status
# ──────────────────────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "target_active,expected_status_str",
    [
        (True, "active"),
        (False, "inactive"),
    ],
    ids=["activate", "deactivate"],
)
def test_set_offer_status_returns_200_on_success(
    admin_api_client: TestClient,
    offer_service_mock: Mock,
    offer_factory: Callable[..., Offer],
    target_active: bool,
    expected_status_str: str,
) -> None:
    # Arrange
    offer = offer_factory(active=target_active)
    offer_service_mock.set_offer_status.return_value = offer
    request_data = {"status": expected_status_str}

    # Act
    response = admin_api_client.patch(
        f"/api/v1/offers/{offer.id}/status", json=request_data
    )

    # Assert
    assert response.status_code == status.HTTP_200_OK
    _assert_offer_status_response(response.json(), offer, expected_status_str)


@pytest.mark.parametrize(
    "exception,expected_status,expected_code",
    [
        (
            OfferNotFoundException("00000000-0000-0000-0000-000000000000"),
            status.HTTP_404_NOT_FOUND,
            ErrorCode.NOT_FOUND,
        ),
        (
            Exception("Unexpected DB failure"),
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            ErrorCode.INTERNAL_SERVER_ERROR,
        ),
    ],
)
def test_set_offer_status_returns_error_on_exception(
    admin_api_client: TestClient,
    offer_service_mock: Mock,
    offer_factory: Callable[..., Offer],
    exception: Exception,
    expected_status: int,
    expected_code: str,
) -> None:
    # Arrange
    offer = offer_factory()
    offer_service_mock.set_offer_status.side_effect = exception

    # Act
    response = admin_api_client.patch(
        f"/api/v1/offers/{offer.id}/status", json={"status": "inactive"}
    )

    # Assert
    assert response.status_code == expected_status
    assert_error_code(response.json(), expected_code)


def test_set_offer_status_returns_404_on_offer_not_found(
    admin_api_client: TestClient,
    offer_service_mock: Mock,
) -> None:
    # Arrange
    missing_offer_id = "00000000-0000-0000-0000-000000000000"
    offer_service_mock.set_offer_status.side_effect = OfferNotFoundException(
        missing_offer_id
    )

    # Act
    response = admin_api_client.patch(
        f"/api/v1/offers/{missing_offer_id}/status", json={"status": "active"}
    )

    # Assert
    assert response.status_code == status.HTTP_404_NOT_FOUND
    data = response.json()
    assert_error_code(data, ErrorCode.NOT_FOUND)
    assert data["error"]["details"]["resource_type"] == "offer"
    assert data["error"]["details"]["resource_id"] == missing_offer_id


def test_set_offer_status_enforces_admin_user(
    non_admin_client: TestClient,
    offer_factory: Callable[..., Offer],
) -> None:
    # Act
    offer = offer_factory()
    response = non_admin_client.patch(
        f"/api/v1/offers/{offer.id}/status", json={"status": "inactive"}
    )

    # Assert
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert_error_code(response.json(), ErrorCode.FORBIDDEN)
