"""Integration tests for GET /api/v1/offers/{id}."""

from datetime import date, timedelta
from typing import Any

import pytest
from fastapi import status
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio

_TODAY = date.today()
_FUTURE = date.today() + timedelta(days=30)


def _offer_payload(merchant_id: str) -> dict[str, Any]:
    return {
        "merchant_id": merchant_id,
        "cashback_type": "percent",
        "cashback_value": 5.0,
        "start_date": _TODAY.isoformat(),
        "end_date": _FUTURE.isoformat(),
        "monthly_cap": 100.0,
    }


async def test_get_offer_details_returns_200_for_active_offer_as_user(
    admin_http_client: AsyncClient,
    user_http_client: AsyncClient,
) -> None:
    # Arrange: create a merchant and active offer as admin
    merchant_res = await admin_http_client.post(
        "/api/v1/merchants/",
        json={"name": "Details Merchant 1", "default_cashback_percentage": 5.0},
    )
    merchant_id = merchant_res.json()["id"]
    offer_res = await admin_http_client.post(
        "/api/v1/offers/",
        json=_offer_payload(merchant_id),
    )
    offer_id = offer_res.json()["id"]

    # Act
    response = await user_http_client.get(f"/api/v1/offers/{offer_id}")

    # Assert
    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert body["merchant_name"] == "Details Merchant 1"
    assert body["cashback_type"] == "percent"


async def test_get_offer_details_returns_200_for_inactive_offer_as_admin(
    admin_http_client: AsyncClient,
) -> None:
    # Arrange: create merchant, offer, then deactivate the offer
    merchant_res = await admin_http_client.post(
        "/api/v1/merchants/",
        json={"name": "Details Merchant 2", "default_cashback_percentage": 5.0},
    )
    merchant_id = merchant_res.json()["id"]
    offer_res = await admin_http_client.post(
        "/api/v1/offers/",
        json=_offer_payload(merchant_id),
    )
    offer_id = offer_res.json()["id"]
    await admin_http_client.patch(
        f"/api/v1/offers/{offer_id}/status",
        json={"status": "inactive"},
    )

    # Act: admin can view inactive offers
    response = await admin_http_client.get(f"/api/v1/offers/{offer_id}")

    # Assert
    assert response.status_code == status.HTTP_200_OK


async def test_get_offer_details_returns_403_for_inactive_offer_as_user(
    admin_http_client: AsyncClient,
    user_http_client: AsyncClient,
) -> None:
    # Arrange: create merchant, offer, deactivate offer
    merchant_res = await admin_http_client.post(
        "/api/v1/merchants/",
        json={"name": "Details Merchant 3", "default_cashback_percentage": 5.0},
    )
    merchant_id = merchant_res.json()["id"]
    offer_res = await admin_http_client.post(
        "/api/v1/offers/",
        json=_offer_payload(merchant_id),
    )
    offer_id = offer_res.json()["id"]
    await admin_http_client.patch(
        f"/api/v1/offers/{offer_id}/status",
        json={"status": "inactive"},
    )

    # Act: regular user cannot view inactive offers
    response = await user_http_client.get(f"/api/v1/offers/{offer_id}")

    # Assert
    assert response.status_code == status.HTTP_403_FORBIDDEN


async def test_get_offer_details_returns_404_on_unknown_offer(
    user_http_client: AsyncClient,
) -> None:
    # Act
    response = await user_http_client.get("/api/v1/offers/00000000-0000-0000-0000-000000000000")

    # Assert
    assert response.status_code == status.HTTP_404_NOT_FOUND
    body = response.json()
    assert body["error"]["details"]["resource_type"] == "offer"


async def test_get_offer_details_returns_401_on_unauthenticated(
    http_client: AsyncClient,
) -> None:
    # Act
    response = await http_client.get("/api/v1/offers/00000000-0000-0000-0000-000000000000")

    # Assert
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
