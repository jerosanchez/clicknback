"""Integration tests for GET /api/v1/users/me/wallet/transactions."""

import pytest
from fastapi import status
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


async def test_list_wallet_transactions_returns_200_empty_for_new_user(
    user_http_client: AsyncClient,
) -> None:
    # Act
    response = await user_http_client.get("/api/v1/users/me/wallet/transactions")

    # Assert
    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert body["pagination"]["total"] == 0
    assert body["data"] == []


async def test_list_wallet_transactions_respects_pagination_params(
    user_http_client: AsyncClient,
) -> None:
    # Act
    response = await user_http_client.get("/api/v1/users/me/wallet/transactions?limit=5&offset=0")

    # Assert
    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert body["pagination"]["total"] == 0


async def test_list_wallet_transactions_returns_401_on_unauthenticated(
    http_client: AsyncClient,
) -> None:
    # Act
    response = await http_client.get("/api/v1/users/me/wallet/transactions")

    # Assert
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
