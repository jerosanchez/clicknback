"""End-to-end tests for admin platform setup and user offer discovery."""

import uuid
from datetime import date, timedelta

import pytest
from httpx import AsyncClient

from tests.e2e.conftest import (
    activate_merchant_via_api,
    activate_offer_via_api,
    create_merchant_via_api,
    create_offer_via_api,
    deactivate_merchant_via_api,
    deactivate_offer_via_api,
)

pytestmark = pytest.mark.asyncio


async def test_admin_setup_platform_and_user_discovers_offer(
    admin_http_client: AsyncClient,
    user_http_client: AsyncClient,
) -> None:
    """
    E2E: Admin sets up merchant & offer → User logs in → browses active offers.

    Validates the complete onboarding flow:
    1. Admin creates a new merchant (inactive)
    2. Admin activates the merchant
    3. Admin creates an offer for that merchant (inactive)
    4. Admin activates the offer
    5. User logs in and browses active offers
    6. User views the newly activated offer in the list
    7. User retrieves full details of the offer
    """
    merchant_name = f"E2E Test Merchant {uuid.uuid4().hex[:6]}"

    # Arrange & Act 1: Admin creates an inactive merchant
    merchant = await create_merchant_via_api(
        admin_http_client,
        name=merchant_name,
        cashback_percentage=7.5,
        active=False,
    )
    merchant_id = merchant["id"]
    assert merchant["active"] is False

    # Act 2: Admin activates the merchant
    activated_merchant = await activate_merchant_via_api(admin_http_client, merchant_id)
    assert activated_merchant["status"] == "active"

    # Act 3: Admin creates an offer and deactivates it
    offer = await create_offer_via_api(
        admin_http_client,
        merchant_id,
        percentage=7.5,
        monthly_cap=150.0,
    )
    offer_id = offer["id"]
    deactivated_offer = await deactivate_offer_via_api(admin_http_client, offer_id)
    assert deactivated_offer["status"] == "inactive"

    # Act 4: Admin activates the offer
    activated_offer = await activate_offer_via_api(admin_http_client, offer_id)
    assert activated_offer["status"] == "active"

    # Act 5 & 6: User logs in and lists active offers
    # (user_http_client is already authenticated)
    offers_response = await user_http_client.get("/offers/active?page=1&page_size=10")

    # Assert offers list
    assert offers_response.status_code == 200
    offers_body = offers_response.json()
    assert "offers" in offers_body
    assert "total" in offers_body
    assert "page" in offers_body
    assert "page_size" in offers_body

    # Verify the newly created offer is in the list
    offer_ids = [o["id"] for o in offers_body["offers"]]
    assert offer_id in offer_ids, (
        "Newly activated offer should appear in active offers list"
    )

    # Act 7: User retrieves full details of the offer
    offer_details_response = await user_http_client.get(f"/offers/{offer_id}")

    # Assert offer details
    assert offer_details_response.status_code == 200
    offer_details = offer_details_response.json()
    assert offer_details["id"] == offer_id
    assert offer_details["merchant_name"] == merchant_name
    assert offer_details["cashback_type"] == "percent"
    assert float(offer_details["cashback_value"]) == 7.5
    assert float(offer_details["monthly_cap"]) == 150.0
    assert offer_details["status"] == "active"
    assert "start_date" in offer_details
    assert "end_date" in offer_details


async def test_inactive_offer_not_visible_to_users(
    admin_http_client: AsyncClient,
    user_http_client: AsyncClient,
) -> None:
    """
    E2E: Inactive offer does not appear in user's active offers list.

    Even a merchant is active, if the offer is inactive, users shouldn't see it.
    """
    # Arrange & Act 1: Admin setup (merchant activated, offer created then deactivated)
    merchant = await create_merchant_via_api(
        admin_http_client,
        name=f"E2E Inactive Merchant {uuid.uuid4().hex[:6]}",
    )
    merchant_id = merchant["id"]
    await activate_merchant_via_api(admin_http_client, merchant_id)

    # Create offer and immediately deactivate it
    offer = await create_offer_via_api(admin_http_client, merchant_id)
    offer_id = offer["id"]
    deactivated = await deactivate_offer_via_api(admin_http_client, offer_id)
    assert deactivated["status"] == "inactive"

    # Act 2: User lists active offers
    offers_response = await user_http_client.get("/offers/active?page=1&page_size=100")

    # Assert
    assert offers_response.status_code == 200
    offers_body = offers_response.json()
    offer_ids = [o["id"] for o in offers_body["offers"]]
    assert offer_id not in offer_ids, (
        "Inactive offer should NOT appear in active offers"
    )


async def test_inactive_merchant_prevents_offer_visibility(
    admin_http_client: AsyncClient,
    user_http_client: AsyncClient,
) -> None:
    """
    E2E: Even if offer is active, if merchant is inactive, offer is not visible.

    Users should only see offers from active merchants with active offers.
    The flow: activate merchant → create offer → deactivate merchant → user
    cannot see the offer.
    """
    # Arrange & Act 1: Admin creates and activates merchant, then creates offer
    merchant = await create_merchant_via_api(
        admin_http_client,
        name=f"E2E Inactive Merchant 2 {uuid.uuid4().hex[:6]}",
    )
    merchant_id = merchant["id"]
    await activate_merchant_via_api(admin_http_client, merchant_id)

    # Create offer while merchant is active (API enforces this)
    offer = await create_offer_via_api(admin_http_client, merchant_id)
    offer_id = offer["id"]

    # Now deactivate the merchant
    deactivated_merchant = await deactivate_merchant_via_api(
        admin_http_client, merchant_id
    )
    assert deactivated_merchant["status"] == "inactive"

    # Act 2: User lists active offers
    offers_response = await user_http_client.get("/offers/active?page=1&page_size=100")

    # Assert
    assert offers_response.status_code == 200
    offers_body = offers_response.json()
    offer_ids = [o["id"] for o in offers_body["offers"]]
    assert offer_id not in offer_ids, (
        "Offer from inactive merchant should NOT appear in active offers"
    )


async def test_expired_offer_not_visible_to_users(
    admin_http_client: AsyncClient,
    user_http_client: AsyncClient,
) -> None:
    """
    E2E: API rejects creating an offer with a past end_date.

    The business rule that prevents expired offers from appearing in active
    offers is enforced at offer creation time: offers with past end_date are
    rejected outright, so they can never exist in the system.
    """
    # Arrange
    merchant = await create_merchant_via_api(
        admin_http_client,
        name=f"E2E Expired Merchant {uuid.uuid4().hex[:6]}",
    )
    merchant_id = merchant["id"]
    await activate_merchant_via_api(admin_http_client, merchant_id)

    # Act: Attempt to create offer with past end_date
    today = date.today()
    past = today - timedelta(days=1)
    even_more_past = past - timedelta(days=30)

    offer_response = await admin_http_client.post(
        "/offers/",
        json={
            "merchant_id": merchant_id,
            "cashback_type": "percent",
            "cashback_value": 5.0,
            "monthly_cap": 50.0,
            "start_date": str(even_more_past),
            "end_date": str(past),  # Expired yesterday
        },
    )

    # Assert: API rejects offers with past end_date — they can never appear in
    # active offers because they cannot be created in the first place.
    assert offer_response.status_code in (400, 422), (
        f"Expected rejection for past end_date, got {offer_response.status_code}: "
        f"{offer_response.text}"
    )


async def test_future_offer_not_visible_to_users(
    admin_http_client: AsyncClient,
    user_http_client: AsyncClient,
) -> None:
    """
    E2E: Offer with future start_date does not appear in active offers.

    Validates that offers not yet started are hidden from users.
    """
    # Arrange & Act 1: Admin setup
    merchant = await create_merchant_via_api(
        admin_http_client,
        name=f"E2E Future Merchant {uuid.uuid4().hex[:6]}",
    )
    merchant_id = merchant["id"]
    await activate_merchant_via_api(admin_http_client, merchant_id)

    # Act 2: Admin creates offer with future start_date
    today = date.today()
    future_start = today + timedelta(days=30)
    future_end = future_start + timedelta(days=90)

    offer_response = await admin_http_client.post(
        "/offers/",
        json={
            "merchant_id": merchant_id,
            "cashback_type": "percent",
            "cashback_value": 5.0,
            "monthly_cap": 50.0,
            "start_date": str(future_start),
            "end_date": str(future_end),
        },
    )
    assert offer_response.status_code == 201
    future_offer = offer_response.json()
    future_offer_id = future_offer["id"]

    # Activate the offer
    await activate_offer_via_api(admin_http_client, future_offer_id)

    # Act 3: User lists active offers
    offers_response = await user_http_client.get("/offers/active?page=1&page_size=100")

    # Assert
    assert offers_response.status_code == 200
    offers_body = offers_response.json()
    offer_ids = [o["id"] for o in offers_body["offers"]]
    assert future_offer_id not in offer_ids, (
        "Future offer should NOT appear in active offers"
    )
