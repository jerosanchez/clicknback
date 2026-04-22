from typing import Any, Callable
from unittest.mock import Mock

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.core.config import settings
from app.core.errors.codes import ErrorCode
from app.offers.models import Offer
from tests.unit.offers.conftest import assert_error_code


def _assert_paginated_offers_response(
    data: dict[str, Any],
    items: list[Offer],
    total: int,
    offset: int,
    limit: int,
) -> None:
    assert data["pagination"]["total"] == total
    assert data["pagination"]["offset"] == offset
    assert data["pagination"]["limit"] == limit
    assert len(data["data"]) == len(items)
    for i, offer in enumerate(items):
        item = data["data"][i]
        assert item["id"] == str(offer.id)
        assert item["merchant_id"] == str(offer.merchant_id)
        expected_cashback_type = (
            "fixed" if offer.fixed_amount is not None else "percent"
        )
        assert item["cashback_type"] == expected_cashback_type
        expected_cashback_value = (
            offer.fixed_amount if offer.fixed_amount is not None else offer.percentage
        )
        assert item["cashback_value"] == expected_cashback_value
        assert item["start_date"] == offer.start_date.isoformat()
        assert item["end_date"] == offer.end_date.isoformat()
        assert item["monthly_cap_per_user"] == offer.monthly_cap_per_user
        assert item["status"] == ("active" if offer.active else "inactive")


# ──────────────────────────────────────────────────────────────────────────────
# GET /api/v1/offers
# ──────────────────────────────────────────────────────────────────────────────


def test_list_offers_returns_200_on_success(
    user_client: TestClient,
    offer_service_mock: Mock,
    offer_factory: Callable[..., Offer],
) -> None:
    # Arrange
    offer_ids = [
        "a0000001-0000-0000-0000-000000000001",
        "a0000002-0000-0000-0000-000000000002",
        "a0000003-0000-0000-0000-000000000003",
    ]
    offers = [offer_factory(id=offer_ids[i]) for i in range(3)]
    offer_service_mock.list_offers.return_value = (offers, 3)

    # Act
    response = user_client.get("/api/v1/offers")

    # Assert
    assert response.status_code == status.HTTP_200_OK
    _assert_paginated_offers_response(
        response.json(), offers, total=3, offset=0, limit=settings.default_page_size
    )


def test_list_offers_returns_200_on_empty_results(
    user_client: TestClient,
    offer_service_mock: Mock,
) -> None:
    # Arrange
    offer_service_mock.list_offers.return_value = ([], 0)

    # Act
    response = user_client.get("/api/v1/offers")

    # Assert
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["pagination"]["total"] == 0
    assert data["data"] == []


def test_list_offers_returns_500_on_unexpected_error(
    user_client: TestClient,
    offer_service_mock: Mock,
) -> None:
    # Arrange
    offer_service_mock.list_offers.side_effect = Exception("Unexpected DB failure")

    # Act
    response = user_client.get("/api/v1/offers")

    # Assert
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert_error_code(response.json(), ErrorCode.INTERNAL_SERVER_ERROR)


def test_list_offers_returns_401_on_unauthenticated_request(
    unauthenticated_client: TestClient,
) -> None:
    # Act
    response = unauthenticated_client.get("/api/v1/offers")

    # Assert
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert_error_code(response.json(), ErrorCode.INVALID_TOKEN)


@pytest.mark.parametrize(
    "query_string",
    [
        "offset=-1",  # below minimum offset
        "limit=0",  # below minimum limit
        f"limit={settings.max_page_size + 1}",  # above maximum limit
    ],
)
def test_list_offers_returns_422_on_invalid_pagination_params(
    user_client: TestClient,
    query_string: str,
) -> None:
    # Act
    response = user_client.get(f"/api/v1/offers?{query_string}")

    # Assert
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    data = response.json()
    assert_error_code(data, ErrorCode.VALIDATION_ERROR)
    assert "violations" in data["error"]["details"]
    assert len(data["error"]["details"]["violations"]) >= 1


@pytest.mark.parametrize(
    "query_string",
    [
        "offset=0",  # minimum offset
        "limit=1",  # minimum limit
        f"limit={settings.default_page_size}",  # default limit
        f"limit={settings.max_page_size}",  # maximum limit
    ],
)
def test_list_offers_returns_200_on_valid_pagination_params(
    user_client: TestClient,
    offer_service_mock: Mock,
    query_string: str,
) -> None:
    # Arrange
    offer_service_mock.list_offers.return_value = ([], 0)

    # Act
    response = user_client.get(f"/api/v1/offers?{query_string}")

    # Assert
    assert response.status_code == status.HTTP_200_OK


def test_list_offers_returns_400_on_invalid_status_filter(
    user_client: TestClient,
) -> None:
    # Arrange
    invalid_status_value = "unknown_status"

    # Act
    response = user_client.get(f"/api/v1/offers?status={invalid_status_value}")

    # Assert
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data = response.json()
    assert_error_code(data, ErrorCode.VALIDATION_ERROR)
    violations = data["error"]["details"]["violations"]
    assert any(v["field"] == "status" for v in violations)


def test_list_offers_returns_400_on_inverted_date_range(
    user_client: TestClient,
) -> None:
    # Arrange
    date_from = "2026-12-31"
    date_to = "2026-01-01"

    # Act
    response = user_client.get(
        f"/api/v1/offers?date_from={date_from}&date_to={date_to}"
    )

    # Assert
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data = response.json()
    assert_error_code(data, ErrorCode.VALIDATION_ERROR)
    violations = data["error"]["details"]["violations"]
    assert any(v["field"] == "date_from" for v in violations)
