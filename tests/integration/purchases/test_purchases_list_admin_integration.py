"""Integration tests for GET /api/v1/purchases/ (admin)."""

import uuid
from datetime import date, timedelta

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
        name=f"Admin List Merchant {uuid.uuid4().hex[:6]}",
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


async def test_list_all_purchases_returns_200_with_pagination_as_admin(
    admin_http_client: AsyncClient,
    user_http_client_with_user: tuple[AsyncClient, User],
    db: AsyncSession,
) -> None:
    # Arrange: ingest a purchase as a regular user
    user_client, user = user_http_client_with_user
    merchant = await _seed_merchant_with_offer(db)
    await user_client.post(
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
    response = await admin_http_client.get("/api/v1/purchases/?offset=0&limit=10")

    # Assert
    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert body["data"]
    assert body["pagination"]["total"] >= 1


async def test_list_all_purchases_returns_empty_list_when_no_purchases(
    admin_http_client: AsyncClient,
) -> None:
    # Act: no purchases exist in this test's isolated transaction
    response = await admin_http_client.get("/api/v1/purchases/?offset=0&limit=10")

    # Assert
    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert body["pagination"]["total"] == 0


async def test_list_all_purchases_returns_401_for_non_admin(
    user_http_client: AsyncClient,
) -> None:
    # Act
    response = await user_http_client.get("/api/v1/purchases/")

    # Assert
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


async def test_list_all_purchases_returns_401_on_unauthenticated(
    http_client: AsyncClient,
) -> None:
    # Act
    response = await http_client.get("/api/v1/purchases/")

    # Assert
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
