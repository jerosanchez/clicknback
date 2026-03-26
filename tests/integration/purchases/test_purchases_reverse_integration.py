"""Integration tests for PATCH /api/v1/purchases/{purchase_id}/reverse."""

import uuid
from datetime import date, timedelta
from decimal import Decimal

import pytest
from fastapi import status
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.merchants.models import Merchant
from app.offers.models import Offer
from app.purchases.models import Purchase
from app.users.models import User

pytestmark = pytest.mark.asyncio

_TODAY = date.today()
_FUTURE = date.today() + timedelta(days=30)


async def _seed_merchant_with_offer(db: AsyncSession) -> tuple[Merchant, Offer]:
    merchant = Merchant(
        name=f"Reverse Merchant {uuid.uuid4().hex[:6]}",
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

    return merchant, offer


async def _seed_purchase(
    db: AsyncSession,
    user: User,
    merchant: Merchant,
    offer: Offer,
    purchase_status: str,
    cashback_amount: Decimal = Decimal("2.50"),
) -> Purchase:
    purchase = Purchase(
        id=str(uuid.uuid4()),
        external_id=f"ext-{uuid.uuid4()}",
        user_id=str(user.id),
        merchant_id=merchant.id,
        offer_id=offer.id,
        amount=Decimal("50.00"),
        cashback_amount=cashback_amount,
        currency="EUR",
        status=purchase_status,
    )
    db.add(purchase)
    await db.flush()
    return purchase


# ──────────────────────────────────────────────────────────────────────────────
# Happy paths
# ──────────────────────────────────────────────────────────────────────────────


async def test_reverse_purchase_returns_200_for_pending_purchase(
    admin_http_client: AsyncClient,
    user_http_client_with_user: tuple[AsyncClient, User],
    db: AsyncSession,
) -> None:
    # Arrange
    _, user = user_http_client_with_user
    merchant, offer = await _seed_merchant_with_offer(db)
    purchase = await _seed_purchase(db, user, merchant, offer, "pending")

    # Act
    response = await admin_http_client.patch(f"/api/v1/purchases/{purchase.id}/reverse")

    # Assert
    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert body["id"] == purchase.id
    assert body["status"] == "reversed"
    assert Decimal(str(body["cashback_amount"])) == Decimal("0")


async def test_reverse_purchase_returns_200_for_confirmed_purchase(
    admin_http_client: AsyncClient,
    user_http_client_with_user: tuple[AsyncClient, User],
    db: AsyncSession,
) -> None:
    # Arrange
    _, user = user_http_client_with_user
    merchant, offer = await _seed_merchant_with_offer(db)
    purchase = await _seed_purchase(db, user, merchant, offer, "confirmed")

    # Act
    response = await admin_http_client.patch(f"/api/v1/purchases/{purchase.id}/reverse")

    # Assert
    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert body["id"] == purchase.id
    assert body["status"] == "reversed"
    assert Decimal(str(body["cashback_amount"])) == Decimal("0")


# ──────────────────────────────────────────────────────────────────────────────
# Failure modes
# ──────────────────────────────────────────────────────────────────────────────


async def test_reverse_purchase_returns_400_for_already_reversed_purchase(
    admin_http_client: AsyncClient,
    user_http_client_with_user: tuple[AsyncClient, User],
    db: AsyncSession,
) -> None:
    # Arrange
    _, user = user_http_client_with_user
    merchant, offer = await _seed_merchant_with_offer(db)
    purchase = await _seed_purchase(
        db, user, merchant, offer, "reversed", cashback_amount=Decimal("0")
    )

    # Act
    response = await admin_http_client.patch(f"/api/v1/purchases/{purchase.id}/reverse")

    # Assert
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    body = response.json()
    assert body["error"]["code"] == "PURCHASE_ALREADY_REVERSED"


async def test_reverse_purchase_returns_404_for_missing_purchase(
    admin_http_client: AsyncClient,
) -> None:
    # Arrange
    nonexistent_id = str(uuid.uuid4())

    # Act
    response = await admin_http_client.patch(
        f"/api/v1/purchases/{nonexistent_id}/reverse"
    )

    # Assert
    assert response.status_code == status.HTTP_404_NOT_FOUND
    body = response.json()
    assert body["error"]["code"] == "NOT_FOUND"


# ──────────────────────────────────────────────────────────────────────────────
# Authorization
# ──────────────────────────────────────────────────────────────────────────────


async def test_reverse_purchase_returns_401_when_unauthenticated(
    http_client: AsyncClient,
) -> None:
    # Act
    response = await http_client.patch(f"/api/v1/purchases/{uuid.uuid4()}/reverse")

    # Assert
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


async def test_reverse_purchase_returns_401_when_not_admin(
    user_http_client: AsyncClient,
) -> None:
    # Act
    response = await user_http_client.patch(f"/api/v1/purchases/{uuid.uuid4()}/reverse")

    # Assert
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
