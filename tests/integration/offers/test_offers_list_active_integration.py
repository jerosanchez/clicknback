"""Integration tests for GET /api/v1/offers/active."""

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


async def test_list_active_offers_returns_200_with_results(
    admin_http_client: AsyncClient,
    user_http_client: AsyncClient,
) -> None:
    # Arrange: create a merchant and an active offer starting today
    merchant_res = await admin_http_client.post(
        "/api/v1/merchants/",
        json={"name": "Active Offer Merchant", "default_cashback_percentage": 5.0},
    )
    merchant_id = merchant_res.json()["id"]
    await admin_http_client.post(
        "/api/v1/offers/",
        json=_offer_payload(merchant_id),
    )

    # Act
    response = await user_http_client.get("/api/v1/offers/active")

    # Assert
    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    offers = body["data"]
    assert body["pagination"]["total"] >= 1
    assert len(offers) >= 1
    offer = next(o for o in offers if o["merchant_name"] == "Active Offer Merchant")
    assert offer["cashback_type"] == "percent"
    assert offer["cashback_value"] == 5.0


async def test_list_active_offers_returns_401_on_unauthenticated(
    http_client: AsyncClient,
) -> None:
    # Act
    response = await http_client.get("/api/v1/offers/active")

    # Assert
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
