"""Integration tests for GET /api/v1/purchases/{id}."""

import uuid
from collections.abc import AsyncGenerator
from datetime import date, timedelta
from decimal import Decimal

import pytest
from fastapi import status
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_db
from app.main import app
from app.merchants.models import Merchant
from app.offers.models import Offer
from app.users.models import User
from tests.integration.conftest import create_user, make_token

pytestmark = pytest.mark.asyncio

_TODAY = date.today()
_FUTURE = date.today() + timedelta(days=30)


async def _seed_merchant_with_offer(db: AsyncSession) -> Merchant:
    merchant = Merchant(
        name=f"Details Purchase Merchant {uuid.uuid4().hex[:6]}",
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


async def _ingest_purchase(client: AsyncClient, user_id: str, merchant_id: str) -> str:
    """Ingest a purchase and return its ID."""
    res = await client.post(
        "/api/v1/purchases/",
        json={
            "external_id": f"ext-{uuid.uuid4()}",
            "user_id": user_id,
            "merchant_id": merchant_id,
            "amount": "50.00",
            "currency": "EUR",
        },
    )
    assert res.status_code == status.HTTP_201_CREATED
    return res.json()["id"]


async def test_get_purchase_details_returns_200_for_owner(
    user_http_client_with_user: tuple[AsyncClient, User],
    db: AsyncSession,
) -> None:
    # Arrange
    client, user = user_http_client_with_user
    merchant = await _seed_merchant_with_offer(db)
    purchase_id = await _ingest_purchase(client, str(user.id), merchant.id)

    # Act
    response = await client.get(f"/api/v1/purchases/{purchase_id}")

    # Assert
    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert body["id"] == purchase_id
    assert body["merchant_name"]
    assert Decimal(str(body["amount"])) == Decimal("50.00")


async def test_get_purchase_details_returns_403_for_non_owner(
    user_http_client_with_user: tuple[AsyncClient, User],
    db: AsyncSession,
) -> None:
    # Arrange
    client, user = user_http_client_with_user
    merchant = await _seed_merchant_with_offer(db)
    purchase_id = await _ingest_purchase(client, str(user.id), merchant.id)
    second_user, _ = await create_user(db, email="second-user@example.com")
    token = make_token(second_user)

    async def _override() -> AsyncGenerator[AsyncSession, None]:
        yield db

    app.dependency_overrides[get_async_db] = _override

    # Act
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        headers={"Authorization": f"Bearer {token}"},
    ) as second_client:
        response = await second_client.get(f"/api/v1/purchases/{purchase_id}")

    # Assert
    assert response.status_code == status.HTTP_403_FORBIDDEN


async def test_get_purchase_details_returns_404_for_unknown_purchase(
    user_http_client_with_user: tuple[AsyncClient, User],
) -> None:
    # Arrange
    client, _user = user_http_client_with_user

    # Act
    response = await client.get(f"/api/v1/purchases/{uuid.uuid4()}")

    # Assert
    assert response.status_code == status.HTTP_404_NOT_FOUND


async def test_get_purchase_details_returns_401_on_unauthenticated(
    http_client: AsyncClient,
) -> None:
    # Act
    response = await http_client.get(f"/api/v1/purchases/{uuid.uuid4()}")

    # Assert
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
