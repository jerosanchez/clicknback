from typing import Any, Callable
from unittest.mock import Mock

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.core.config import settings
from app.core.errors.codes import ErrorCode
from app.offers.models import Offer
from tests.unit.offers.conftest import assert_error_code


def _assert_active_offers_response(
    data: dict[str, Any],
    items: list[tuple[Offer, str]],
    total: int,
    offset: int,
    limit: int,
) -> None:
    assert data["pagination"]["total"] == total
    assert data["pagination"]["offset"] == offset
    assert data["pagination"]["limit"] == limit
    assert len(data["data"]) == len(items)
    for i, (offer, merchant_name) in enumerate(items):
        item = data["data"][i]
        assert item["id"] == str(offer.id)
        assert item["merchant_name"] == merchant_name
        expected_cashback_type = (
            "fixed" if offer.fixed_amount is not None else "percent"
        )
        assert item["cashback_type"] == expected_cashback_type
        expected_cashback_value = (
            offer.fixed_amount if offer.fixed_amount is not None else offer.percentage
        )
        assert item["cashback_value"] == expected_cashback_value
        assert item["monthly_cap"] == offer.monthly_cap_per_user
        assert item["start_date"] == offer.start_date.isoformat()
        assert item["end_date"] == offer.end_date.isoformat()


# ──────────────────────────────────────────────────────────────────────────────
# GET /api/v1/offers/active
# ──────────────────────────────────────────────────────────────────────────────


def test_list_active_offers_returns_200_on_success(
    user_client: TestClient,
    offer_service_mock: Mock,
    offer_factory: Callable[..., Offer],
) -> None:
    # Arrange
    offer_ids = [
        "a0000001-0000-0000-0000-000000000001",
        "a0000002-0000-0000-0000-000000000002",
    ]
    merchant_names = ["Shoply", "QuickCart"]
    offers = [offer_factory(id=offer_ids[i]) for i in range(2)]
    items: list[tuple[Offer, str]] = list(zip(offers, merchant_names))
    offer_service_mock.list_active_offers.return_value = (items, 2)

    # Act
    response = user_client.get("/api/v1/offers/active")

    # Assert
    assert response.status_code == status.HTTP_200_OK
    _assert_active_offers_response(
        response.json(),
        items,
        total=2,
        offset=0,
        limit=settings.default_page_size,
    )


def test_list_active_offers_maps_fixed_cashback_correctly(
    user_client: TestClient,
    offer_service_mock: Mock,
    offer_factory: Callable[..., Offer],
) -> None:
    # Arrange
    fixed_offer = offer_factory(percentage=0.0, fixed_amount=5.0)
    merchant_name = "QuickCart"
    items: list[tuple[Offer, str]] = [(fixed_offer, merchant_name)]
    offer_service_mock.list_active_offers.return_value = (items, 1)

    # Act
    response = user_client.get("/api/v1/offers/active")

    # Assert
    assert response.status_code == status.HTTP_200_OK
    _assert_active_offers_response(
        response.json(),
        items,
        total=1,
        offset=0,
        limit=settings.default_page_size,
    )


def test_list_active_offers_returns_200_on_empty_results(
    user_client: TestClient,
    offer_service_mock: Mock,
) -> None:
    # Arrange
    offer_service_mock.list_active_offers.return_value = ([], 0)

    # Act
    response = user_client.get("/api/v1/offers/active")

    # Assert
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["pagination"]["total"] == 0
    assert data["data"] == []


@pytest.mark.parametrize(
    "exception,expected_status,expected_code",
    [
        (
            Exception("Unexpected DB failure"),
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            ErrorCode.INTERNAL_SERVER_ERROR,
        ),
    ],
)
def test_list_active_offers_returns_error_on_exception(
    user_client: TestClient,
    offer_service_mock: Mock,
    exception: Exception,
    expected_status: int,
    expected_code: str,
) -> None:
    # Arrange
    offer_service_mock.list_active_offers.side_effect = exception

    # Act
    response = user_client.get("/api/v1/offers/active")

    # Assert
    assert response.status_code == expected_status
    assert_error_code(response.json(), expected_code)


@pytest.mark.parametrize(
    "query_string",
    [
        "offset=-1",  # below minimum offset
        "limit=0",  # below minimum limit
        f"limit={settings.max_page_size + 1}",  # above maximum limit
    ],
)
def test_list_active_offers_returns_422_on_invalid_pagination_params(
    user_client: TestClient,
    query_string: str,
) -> None:
    # Act
    response = user_client.get(f"/api/v1/offers/active?{query_string}")

    # Assert
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


@pytest.mark.parametrize(
    "query_string",
    [
        "offset=0",  # minimum valid offset
        "limit=1",  # minimum valid limit
        f"limit={settings.default_page_size}",  # default limit
        f"limit={settings.max_page_size}",  # maximum valid limit
    ],
)
def test_list_active_offers_returns_200_on_valid_pagination_params(
    user_client: TestClient,
    offer_service_mock: Mock,
    query_string: str,
) -> None:
    # Arrange
    offer_service_mock.list_active_offers.return_value = ([], 0)

    # Act
    response = user_client.get(f"/api/v1/offers/active?{query_string}")

    # Assert
    assert response.status_code == status.HTTP_200_OK
