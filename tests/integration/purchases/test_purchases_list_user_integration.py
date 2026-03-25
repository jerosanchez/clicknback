"""Integration tests for GET /api/v1/users/me/purchases."""

import uuid
from datetime import date, timedelta
from decimal import Decimal

import pytest
from fastapi import status
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.merchants.models import Merchant
from app.offers.models import Offer
from app.users.models import User

pytestmark = pytest.mark.asyncio

_TODAY = date.today()
_FUTURE = date.today() + timedelta(days=30)


async def _seed_merchant_with_offer(db: AsyncSession) -> Merchant:
    merchant = Merchant(
        name=f"User List Merchant {uuid.uuid4().hex[:6]}",
        default_cashback_percentage=5.0,
        active=True,
    )
    db.add(merchant)
    await db.flush()

    offer = Offer(
        merchant_id=merchant.id,
        percentage=5.0,
        fixed_amount=None,
        start_date=_TODAY,
        end_date=_FUTURE,
        monthly_cap_per_user=100.0,
        active=True,
    )
    db.add(offer)
    await db.flush()

    return merchant


async def test_list_user_purchases_returns_200_with_seeded_purchase(
    user_http_client_with_user: tuple[AsyncClient, User],
    db: AsyncSession,
) -> None:
    # Arrange: ingest a purchase
    client, user = user_http_client_with_user
    merchant = await _seed_merchant_with_offer(db)
    await client.post(
        "/api/v1/purchases/",
        json={
            "external_id": f"ext-{uuid.uuid4()}",
            "user_id": str(user.id),
            "merchant_id": merchant.id,
            "amount": "50.00",
            "currency": "EUR",
        },
    )

    # Act
    response = await client.get("/api/v1/users/me/purchases")

    # Assert
    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert body["total"] >= 1
    assert len(body["items"]) >= 1
    item = body["items"][0]
    assert item["merchant_name"]
    assert Decimal(str(item["amount"])) == Decimal("50.00")


async def test_list_user_purchases_returns_empty_for_new_user(
    user_http_client: AsyncClient,
) -> None:
    # Act: new user with no purchases
    response = await user_http_client.get("/api/v1/users/me/purchases")

    # Assert
    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert body["total"] == 0
    assert body["items"] == []


async def test_list_user_purchases_returns_401_on_unauthenticated(
    http_client: AsyncClient,
) -> None:
    # Act
    response = await http_client.get("/api/v1/users/me/purchases")

    # Assert
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
