"""Integration tests for PATCH /api/v1/offers/{id}/status."""

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


async def _create_merchant_with_offer(admin_client: AsyncClient, merchant_name: str) -> tuple[str, str]:
    """Create a merchant and an offer; return (merchant_id, offer_id)."""
    merchant_res = await admin_client.post(
        "/api/v1/merchants/",
        json={"name": merchant_name, "default_cashback_percentage": 5.0},
    )
    merchant_id = merchant_res.json()["id"]
    offer_res = await admin_client.post(
        "/api/v1/offers/",
        json=_offer_payload(merchant_id),
    )
    offer_id = offer_res.json()["id"]
    return merchant_id, offer_id


async def test_set_offer_status_deactivates_offer(
    admin_http_client: AsyncClient,
) -> None:
    # Arrange
    _, offer_id = await _create_merchant_with_offer(admin_http_client, "Status Offer M1")

    # Act
    response = await admin_http_client.patch(
        f"/api/v1/offers/{offer_id}/status",
        json={"status": "inactive"},
    )

    # Assert
    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert str(body["id"]) == offer_id
    assert body["status"] == "inactive"


async def test_set_offer_status_activates_offer(
    admin_http_client: AsyncClient,
) -> None:
    # Arrange: create and deactivate
    _, offer_id = await _create_merchant_with_offer(admin_http_client, "Status Offer M2")
    await admin_http_client.patch(
        f"/api/v1/offers/{offer_id}/status",
        json={"status": "inactive"},
    )

    # Act: reactivate
    response = await admin_http_client.patch(
        f"/api/v1/offers/{offer_id}/status",
        json={"status": "active"},
    )

    # Assert
    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert body["status"] == "active"


async def test_set_offer_status_returns_404_on_unknown_offer(
    admin_http_client: AsyncClient,
) -> None:
    # Act
    response = await admin_http_client.patch(
        "/api/v1/offers/00000000-0000-0000-0000-000000000000/status",
        json={"status": "inactive"},
    )

    # Assert
    assert response.status_code == status.HTTP_404_NOT_FOUND
    body = response.json()
    assert body["error"]["details"]["resource_type"] == "offer"


async def test_set_offer_status_returns_401_on_non_admin(
    user_http_client: AsyncClient,
) -> None:
    # Act
    response = await user_http_client.patch(
        "/api/v1/offers/some-id/status",
        json={"status": "active"},
    )

    # Assert
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
