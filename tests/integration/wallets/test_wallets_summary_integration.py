"""Integration tests for GET /api/v1/users/me/wallet."""

from decimal import Decimal

import pytest
from fastapi import status
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


async def test_get_wallet_summary_returns_200_with_zero_balances_for_new_user(
    user_http_client: AsyncClient,
) -> None:
    # Act: a new user with no cashback activity
    response = await user_http_client.get("/api/v1/users/me/wallet")

    # Assert
    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert Decimal(str(body["pending_balance"])) == Decimal("0")
    assert Decimal(str(body["available_balance"])) == Decimal("0")
    assert Decimal(str(body["paid_balance"])) == Decimal("0")


async def test_get_wallet_summary_returns_401_on_unauthenticated(
    http_client: AsyncClient,
) -> None:
    # Act
    response = await http_client.get("/api/v1/users/me/wallet")

    # Assert
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
