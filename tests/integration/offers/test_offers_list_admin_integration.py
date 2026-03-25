"""Integration tests for GET /api/v1/offers/ (admin)."""

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


async def test_list_offers_admin_returns_200_with_pagination(
    admin_http_client: AsyncClient,
) -> None:
    # Arrange: create a merchant and an offer
    merchant_res = await admin_http_client.post(
        "/api/v1/merchants/",
        json={
            "name": "List Offer Merchant Alpha",
            "default_cashback_percentage": 5.0,
        },
    )
    merchant_id = merchant_res.json()["id"]
    await admin_http_client.post(
        "/api/v1/offers/",
        json=_offer_payload(merchant_id),
    )

    # Act
    response = await admin_http_client.get("/api/v1/offers/?page=1&page_size=10")

    # Assert
    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert body["items"]
    assert body["total"] >= 1


async def test_list_offers_admin_returns_401_on_non_admin(
    user_http_client: AsyncClient,
) -> None:
    # Act
    response = await user_http_client.get("/api/v1/offers/")

    # Assert
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
