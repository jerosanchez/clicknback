"""Integration tests for POST /api/v1/offers/."""

from datetime import date, timedelta
from typing import Any

import pytest
from fastapi import status
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio

_TOMORROW = date.today() + timedelta(days=1)
_FUTURE = date.today() + timedelta(days=30)


def _offer_payload(merchant_id: str) -> dict[str, Any]:
    return {
        "merchant_id": merchant_id,
        "cashback_type": "percent",
        "cashback_value": 5.0,
        "start_date": _TOMORROW.isoformat(),
        "end_date": _FUTURE.isoformat(),
        "monthly_cap": 100.0,
    }


async def _create_merchant(admin_client: AsyncClient, name: str) -> str:
    res = await admin_client.post(
        "/api/v1/merchants/",
        json={"name": name, "default_cashback_percentage": 5.0},
    )
    return res.json()["id"]


async def test_create_offer_returns_201_on_success(
    admin_http_client: AsyncClient,
) -> None:
    # Arrange
    merchant_id = await _create_merchant(admin_http_client, "Create Offer Merchant")

    # Act
    response = await admin_http_client.post(
        "/api/v1/offers/",
        json=_offer_payload(merchant_id),
    )

    # Assert
    assert response.status_code == status.HTTP_201_CREATED
    body = response.json()
    assert str(body["merchant_id"]) == merchant_id
    assert body["cashback_type"] == "percent"
    assert body["cashback_value"] == 5.0
    assert body["start_date"] == _TOMORROW.isoformat()
    assert body["end_date"] == _FUTURE.isoformat()
    assert body["monthly_cap_per_user"] == 100.0
    assert body["status"] == "active"


async def test_create_offer_returns_404_on_unknown_merchant(
    admin_http_client: AsyncClient,
) -> None:
    # Act
    response = await admin_http_client.post(
        "/api/v1/offers/",
        json=_offer_payload("00000000-0000-0000-0000-000000000000"),
    )

    # Assert
    assert response.status_code == status.HTTP_404_NOT_FOUND
    body = response.json()
    assert body["error"]["details"]["resource_type"] == "merchant"


async def test_create_offer_returns_422_on_inactive_merchant(
    admin_http_client: AsyncClient,
) -> None:
    # Arrange: create and immediately deactivate a merchant
    merchant_id = await _create_merchant(admin_http_client, "Inactive Offer Merchant")
    await admin_http_client.patch(
        f"/api/v1/merchants/{merchant_id}/status",
        json={"status": "inactive"},
    )

    # Act
    response = await admin_http_client.post(
        "/api/v1/offers/",
        json=_offer_payload(merchant_id),
    )

    # Assert
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    body = response.json()
    assert body["error"]["code"] == "MERCHANT_NOT_ACTIVE"


async def test_create_offer_returns_409_on_duplicate_active_offer(
    admin_http_client: AsyncClient,
) -> None:
    # Arrange: create merchant and first offer
    merchant_id = await _create_merchant(admin_http_client, "Duplicate Offer Merchant")
    first = await admin_http_client.post(
        "/api/v1/offers/",
        json=_offer_payload(merchant_id),
    )
    assert first.status_code == status.HTTP_201_CREATED

    # Act: try to create a second active offer for the same merchant
    response = await admin_http_client.post(
        "/api/v1/offers/",
        json=_offer_payload(merchant_id),
    )

    # Assert
    assert response.status_code == status.HTTP_409_CONFLICT
    body = response.json()
    assert body["error"]["code"] == "ACTIVE_OFFER_ALREADY_EXISTS"


async def test_create_offer_returns_401_on_non_admin(
    user_http_client: AsyncClient,
) -> None:
    # Act
    response = await user_http_client.post(
        "/api/v1/offers/",
        json=_offer_payload("00000000-0000-0000-0000-000000000000"),
    )

    # Assert
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
