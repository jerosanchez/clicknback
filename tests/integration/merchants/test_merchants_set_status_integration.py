"""Integration tests for PATCH /api/v1/merchants/{id}/status."""

import pytest
from fastapi import status
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


async def test_set_merchant_status_deactivates_merchant(
    admin_http_client: AsyncClient,
) -> None:
    # Arrange
    create_res = await admin_http_client.post(
        "/api/v1/merchants/",
        json={"name": "Status Test Merchant", "default_cashback_percentage": 3.0},
    )
    merchant_id = create_res.json()["id"]

    # Act
    response = await admin_http_client.patch(
        f"/api/v1/merchants/{merchant_id}/status",
        json={"status": "inactive"},
    )

    # Assert
    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert str(body["id"]) == merchant_id
    assert body["status"] == "inactive"


async def test_set_merchant_status_activates_merchant(
    admin_http_client: AsyncClient,
) -> None:
    # Arrange: create and deactivate
    create_res = await admin_http_client.post(
        "/api/v1/merchants/",
        json={
            "name": "Reactivate Test Merchant",
            "default_cashback_percentage": 3.0,
        },
    )
    merchant_id = create_res.json()["id"]
    await admin_http_client.patch(
        f"/api/v1/merchants/{merchant_id}/status",
        json={"status": "inactive"},
    )

    # Act: reactivate
    response = await admin_http_client.patch(
        f"/api/v1/merchants/{merchant_id}/status",
        json={"status": "active"},
    )

    # Assert
    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert body["status"] == "active"


async def test_set_merchant_status_returns_404_on_unknown_merchant(
    admin_http_client: AsyncClient,
) -> None:
    # Act
    response = await admin_http_client.patch(
        "/api/v1/merchants/00000000-0000-0000-0000-000000000000/status",
        json={"status": "active"},
    )

    # Assert
    assert response.status_code == status.HTTP_404_NOT_FOUND
    body = response.json()
    assert body["error"]["details"]["resource_type"] == "merchant"


async def test_set_merchant_status_returns_401_on_non_admin(
    user_http_client: AsyncClient,
) -> None:
    # Act
    response = await user_http_client.patch(
        "/api/v1/merchants/some-id/status",
        json={"status": "active"},
    )

    # Assert
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
