"""Integration tests for POST /api/v1/merchants/."""

from typing import Any

import pytest
from fastapi import status
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


def _payload() -> dict[str, Any]:
    return {"name": "Acme Corp", "default_cashback_percentage": 5.0}


async def test_create_merchant_returns_201_on_success(
    admin_http_client: AsyncClient,
) -> None:
    # Act
    response = await admin_http_client.post("/api/v1/merchants/", json=_payload())

    # Assert
    assert response.status_code == status.HTTP_201_CREATED
    body = response.json()
    assert body["name"] == "Acme Corp"
    assert body["default_cashback_percentage"] == 5.0
    assert body["active"] is True


async def test_create_merchant_returns_401_on_unauthenticated(
    http_client: AsyncClient,
) -> None:
    # Act
    response = await http_client.post("/api/v1/merchants/", json=_payload())

    # Assert
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


async def test_create_merchant_returns_401_on_non_admin(
    user_http_client: AsyncClient,
) -> None:
    # Act
    response = await user_http_client.post("/api/v1/merchants/", json=_payload())

    # Assert
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


async def test_create_merchant_returns_409_on_invalid_percentage(
    admin_http_client: AsyncClient,
) -> None:
    # Act: percentage above MAX_CASHBACK_PERCENTAGE (20)
    response = await admin_http_client.post(
        "/api/v1/merchants/",
        json={"name": "Too Generous Corp", "default_cashback_percentage": 25.0},
    )

    # Assert
    assert response.status_code == status.HTTP_409_CONFLICT
    body = response.json()
    assert body["error"]["code"] == "VALIDATION_ERROR"
