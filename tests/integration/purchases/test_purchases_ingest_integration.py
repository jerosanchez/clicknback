"""Integration tests for POST /api/v1/purchases/."""

import uuid
from datetime import date, timedelta
from decimal import Decimal
from typing import Any

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
    """Insert an active merchant and a valid active offer into the test session."""
    merchant = Merchant(
        name=f"Purchase Merchant {uuid.uuid4().hex[:6]}",
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


def _payload(user_id: str, merchant_id: str, external_id: str) -> dict[str, Any]:
    return {
        "external_id": external_id,
        "user_id": user_id,
        "merchant_id": merchant_id,
        "amount": "50.00",
        "currency": "EUR",
    }


async def test_ingest_purchase_returns_201_on_success(
    user_http_client_with_user: tuple[AsyncClient, User],
    db: AsyncSession,
) -> None:
    # Arrange
    client, user = user_http_client_with_user
    merchant = await _seed_merchant_with_offer(db)
    external_id = f"ext-{uuid.uuid4()}"

    # Act
    response = await client.post(
        "/api/v1/purchases/",
        json=_payload(str(user.id), merchant.id, external_id),
    )

    # Assert
    assert response.status_code == status.HTTP_201_CREATED
    body = response.json()
    assert body["status"] == "pending"
    assert Decimal(str(body["cashback_amount"])) > Decimal("0")


async def test_ingest_purchase_returns_409_on_duplicate_external_id(
    user_http_client_with_user: tuple[AsyncClient, User],
    db: AsyncSession,
) -> None:
    # Arrange: ingest once successfully
    client, user = user_http_client_with_user
    merchant = await _seed_merchant_with_offer(db)
    external_id = f"dup-{uuid.uuid4()}"
    first = await client.post(
        "/api/v1/purchases/",
        json=_payload(str(user.id), merchant.id, external_id),
    )
    assert first.status_code == status.HTTP_201_CREATED

    # Act: ingest same external_id again
    response = await client.post(
        "/api/v1/purchases/",
        json=_payload(str(user.id), merchant.id, external_id),
    )

    # Assert
    assert response.status_code == status.HTTP_409_CONFLICT
    body = response.json()
    assert body["error"]["code"] == "DUPLICATE_PURCHASE"
    assert body["error"]["details"]["external_id"] == external_id


async def test_ingest_purchase_returns_403_on_wrong_user_id(
    user_http_client_with_user: tuple[AsyncClient, User],
    db: AsyncSession,
) -> None:
    # Arrange: user tries to ingest on behalf of a different user
    client, _authenticated_user = user_http_client_with_user
    merchant = await _seed_merchant_with_offer(db)
    other_user_id = str(uuid.uuid4())

    # Act
    response = await client.post(
        "/api/v1/purchases/",
        json=_payload(other_user_id, merchant.id, f"ext-{uuid.uuid4()}"),
    )

    # Assert
    assert response.status_code == status.HTTP_403_FORBIDDEN


async def test_ingest_purchase_returns_401_on_unauthenticated(
    http_client: AsyncClient,
    db: AsyncSession,
) -> None:
    # Arrange
    merchant = await _seed_merchant_with_offer(db)

    # Act
    response = await http_client.post(
        "/api/v1/purchases/",
        json=_payload(str(uuid.uuid4()), merchant.id, f"ext-{uuid.uuid4()}"),
    )

    # Assert
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
