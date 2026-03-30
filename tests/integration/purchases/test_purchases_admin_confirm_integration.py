"""Integration tests for POST /api/v1/purchases/{purchase_id}/confirmation."""

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
        name=f"Admin Confirm Merchant {uuid.uuid4().hex[:6]}",
        default_cashback_percentage=10.0,
        active=True,
    )
    db.add(merchant)
    await db.flush()

    offer = Offer(
        merchant_id=merchant.id,
        percentage=10.0,
        fixed_amount=None,
        start_date=_TODAY,
        end_date=_FUTURE,
        monthly_cap_per_user=1000.0,
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
    cashback_amount: Decimal = Decimal("10.00"),
) -> Purchase:
    purchase = Purchase(
        id=str(uuid.uuid4()),
        external_id=f"ext-{uuid.uuid4()}",
        user_id=str(user.id),
        merchant_id=merchant.id,
        offer_id=offer.id,
        amount=Decimal("100.00"),
        cashback_amount=cashback_amount,
        currency="EUR",
        status="pending",
    )
    db.add(purchase)
    await db.flush()
    return purchase


# ──────────────────────────────────────────────────────────────────────────────
# Happy paths
# ──────────────────────────────────────────────────────────────────────────────


async def test_admin_confirm_purchase_returns_200_for_pending_purchase(
    admin_http_client: AsyncClient,
    user_http_client_with_user: tuple[AsyncClient, User],
    db: AsyncSession,
) -> None:
    # Arrange
    _, user = user_http_client_with_user
    merchant, offer = await _seed_merchant_with_offer(db)
    purchase = await _seed_purchase(db, user, merchant, offer)

    # Act
    response = await admin_http_client.post(
        f"/api/v1/purchases/{purchase.id}/confirmation"
    )

    # Assert
    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert body["id"] == purchase.id
    assert body["status"] == "confirmed"
    assert Decimal(str(body["cashback_amount"])) == Decimal("10.00")


async def test_admin_confirm_purchase_returns_all_fields_in_response(
    admin_http_client: AsyncClient,
    user_http_client_with_user: tuple[AsyncClient, User],
    db: AsyncSession,
) -> None:
    # Arrange
    _, user = user_http_client_with_user
    merchant, offer = await _seed_merchant_with_offer(db)
    purchase = await _seed_purchase(
        db, user, merchant, offer, cashback_amount=Decimal("5.50")
    )

    # Act
    response = await admin_http_client.post(
        f"/api/v1/purchases/{purchase.id}/confirmation"
    )

    # Assert
    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert "id" in body
    assert "status" in body
    assert "cashback_amount" in body
    assert body["status"] == "confirmed"
    assert Decimal(str(body["cashback_amount"])) == Decimal("5.50")


# ──────────────────────────────────────────────────────────────────────────────
# Authorization failures (401, 403)
# ──────────────────────────────────────────────────────────────────────────────


async def test_admin_confirm_purchase_returns_401_for_unauthenticated_user(
    http_client: AsyncClient,
) -> None:
    # Act
    response = await http_client.post(f"/api/v1/purchases/{uuid.uuid4()}/confirmation")

    # Assert
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


async def test_admin_confirm_purchase_returns_401_for_non_admin_user(
    user_http_client: AsyncClient,
) -> None:
    # Act
    response = await user_http_client.post(
        f"/api/v1/purchases/{uuid.uuid4()}/confirmation"
    )

    # Assert
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


# ──────────────────────────────────────────────────────────────────────────────
# Validation failures (422, 404)
# ──────────────────────────────────────────────────────────────────────────────


async def test_admin_confirm_purchase_returns_404_for_nonexistent_purchase(
    admin_http_client: AsyncClient,
) -> None:
    # Arrange
    nonexistent_purchase_id = str(uuid.uuid4())

    # Act
    response = await admin_http_client.post(
        f"/api/v1/purchases/{nonexistent_purchase_id}/confirmation"
    )

    # Assert
    assert response.status_code == status.HTTP_404_NOT_FOUND
    body = response.json()
    assert body["error"]["code"] == "NOT_FOUND"
    assert nonexistent_purchase_id in body["error"]["message"]


async def test_admin_confirm_purchase_returns_422_for_non_pending_purchase(
    admin_http_client: AsyncClient,
    user_http_client_with_user: tuple[AsyncClient, User],
    db: AsyncSession,
) -> None:
    # Arrange
    _, user = user_http_client_with_user
    merchant, offer = await _seed_merchant_with_offer(db)
    purchase = await _seed_purchase(db, user, merchant, offer)

    # First, confirm the purchase
    await admin_http_client.post(f"/api/v1/purchases/{purchase.id}/confirmation")

    # Act: Try to confirm it again
    response = await admin_http_client.post(
        f"/api/v1/purchases/{purchase.id}/confirmation"
    )

    # Assert
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    body = response.json()
    assert body["error"]["code"] == "PURCHASE_NOT_PENDING"
    assert "confirmed" in body["error"]["message"].lower()


async def test_admin_confirm_purchase_returns_422_for_reversed_purchase(
    admin_http_client: AsyncClient,
    user_http_client_with_user: tuple[AsyncClient, User],
    db: AsyncSession,
) -> None:
    # Arrange
    _, user = user_http_client_with_user
    merchant, offer = await _seed_merchant_with_offer(db)

    reversed_purchase = Purchase(
        id=str(uuid.uuid4()),
        external_id=f"ext-{uuid.uuid4()}",
        user_id=str(user.id),
        merchant_id=merchant.id,
        offer_id=offer.id,
        amount=Decimal("100.00"),
        cashback_amount=Decimal("0"),
        currency="EUR",
        status="reversed",
    )
    db.add(reversed_purchase)
    await db.flush()

    # Act
    response = await admin_http_client.post(
        f"/api/v1/purchases/{reversed_purchase.id}/confirmation"
    )

    # Assert
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    body = response.json()
    assert body["error"]["code"] == "PURCHASE_NOT_PENDING"
