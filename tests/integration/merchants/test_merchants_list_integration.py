"""Integration tests for GET /api/v1/merchants/."""

import pytest
from fastapi import status
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


async def test_list_merchants_returns_200_with_pagination(
    admin_http_client: AsyncClient,
) -> None:
    # Arrange: create two merchants
    await admin_http_client.post(
        "/api/v1/merchants/",
        json={"name": "Merchant Alpha", "default_cashback_percentage": 3.0},
    )
    await admin_http_client.post(
        "/api/v1/merchants/",
        json={"name": "Merchant Beta", "default_cashback_percentage": 4.0},
    )

    # Act
    response = await admin_http_client.get("/api/v1/merchants/?page=1&page_size=10")

    # Assert
    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert body["items"]
    assert body["total"] >= 2
    assert body["page"] == 1
    assert body["page_size"] == 10


async def test_list_merchants_filters_by_active_status(
    admin_http_client: AsyncClient,
) -> None:
    # Arrange: create one active and one inactive merchant
    await admin_http_client.post(
        "/api/v1/merchants/",
        json={"name": "Active Merchant", "default_cashback_percentage": 3.0},
    )
    inactive_res = await admin_http_client.post(
        "/api/v1/merchants/",
        json={"name": "Inactive Merchant", "default_cashback_percentage": 3.0},
    )
    inactive_id = inactive_res.json()["id"]
    await admin_http_client.patch(
        f"/api/v1/merchants/{inactive_id}/status",
        json={"status": "inactive"},
    )

    # Act
    response = await admin_http_client.get("/api/v1/merchants/?active=true")

    # Assert
    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert len(body["items"]) > 0
    assert all(item["active"] for item in body["items"])


async def test_list_merchants_returns_401_on_unauthenticated(
    http_client: AsyncClient,
) -> None:
    # Act
    response = await http_client.get("/api/v1/merchants/")

    # Assert
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


async def test_list_merchants_returns_401_on_non_admin(
    user_http_client: AsyncClient,
) -> None:
    # Act
    response = await user_http_client.get("/api/v1/merchants/")

    # Assert
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
