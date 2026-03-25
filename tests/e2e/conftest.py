"""
Shared fixtures for end-to-end tests.

Requires Docker Compose to spin up the full stack: PostgreSQL, migrations, and
the FastAPI application.

Isolation strategy
------------------
Each test creates its own data through the HTTP API (no direct DB inserts).
No pre-seeded state is assumed; every test is self-contained and idempotent.
Tests can safely run in parallel if desired (each uses unique UUIDs for isolation).
"""

import asyncio
import os
import uuid
from collections.abc import AsyncGenerator
from typing import Any

import httpx
import pytest_asyncio
from httpx import AsyncClient

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# Port exposed by docker-compose.e2e.yml; override via E2E_APP_PORT env var.
_APP_PORT = os.environ.get("E2E_APP_PORT", "8002")
_BASE_URL = f"http://localhost:{_APP_PORT}/api/v1"
_HEALTH_URL = f"http://localhost:{_APP_PORT}/health/ready"


# ---------------------------------------------------------------------------
# Stack health guard (session-scoped)
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture(scope="session", autouse=True)
async def ensure_api_healthy() -> AsyncGenerator[None, None]:
    """
    Session-scoped guard: polls the API health endpoint until it responds or
    times out.  Fails fast with a clear message if the E2E stack is not up.

    The stack lifecycle is managed externally by the Makefile targets
    `e2e-stack-up` and `e2e-stack-down` (called by `make test-e2e`).
    Run `make e2e-stack-up` before invoking pytest directly.
    """
    timeout_seconds = 60
    async with httpx.AsyncClient() as client:
        for _ in range(timeout_seconds * 2):  # poll every 0.5 s
            try:
                resp = await client.get(_HEALTH_URL, timeout=2)
                if resp.status_code == 200:
                    yield
                    return
            except (httpx.ConnectError, httpx.TimeoutException):
                pass
            await asyncio.sleep(0.5)
    raise TimeoutError(
        f"E2E API at {_HEALTH_URL} did not become healthy within {timeout_seconds}s. "
        "Run `make e2e-stack-up` first."
    )


# ---------------------------------------------------------------------------
# Base unauthenticated client (function-scoped)
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture()
async def http_client() -> AsyncGenerator[AsyncClient, None]:
    """
    Unauthenticated httpx.AsyncClient targeting the live API.

    Test data is created through API calls, not DB inserts.
    """
    async with AsyncClient(base_url=_BASE_URL) as client:
        yield client


# ---------------------------------------------------------------------------
# Authenticated clients (function-scoped)
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture()
async def user_http_client(
    http_client: AsyncClient,
) -> AsyncGenerator[AsyncClient, None]:
    """
    Authenticated AsyncClient with a regular-user Bearer token.

    Creates a real user account via the API and attaches their JWT to
    every request.
    """
    email = f"e2e-user-{uuid.uuid4().hex[:8]}@example.com"
    password = "ValidPass1!"

    # Register the user
    register_resp = await http_client.post(
        "/users/",
        json={
            "email": email,
            "password": password,
        },
    )
    assert register_resp.status_code == 201, (
        f"Registration failed: {register_resp.text}"
    )

    # Login to get token
    login_resp = await http_client.post(
        "/auth/login",
        json={
            "email": email,
            "password": password,
        },
    )
    assert login_resp.status_code == 200, f"Login failed: {login_resp.text}"
    token = login_resp.json()["access_token"]

    # Create authenticated client
    async with AsyncClient(
        base_url=_BASE_URL,
        headers={"Authorization": f"Bearer {token}"},
    ) as client:
        yield client


@pytest_asyncio.fixture()
async def admin_http_client(
    http_client: AsyncClient,
) -> AsyncGenerator[AsyncClient, None]:
    """
    Authenticated AsyncClient with an admin Bearer token.

    Uses a pre-seeded admin account (carol@clicknback.com) from seeds/all.sql.
    """
    email = "carol@clicknback.com"
    password = "Str0ng!Pass"

    # Login with pre-seeded admin credentials
    login_resp = await http_client.post(
        "/auth/login",
        json={
            "email": email,
            "password": password,
        },
    )
    assert login_resp.status_code == 200, f"Admin login failed: {login_resp.text}"
    token = login_resp.json()["access_token"]

    # Create authenticated client
    async with AsyncClient(
        base_url=_BASE_URL,
        headers={"Authorization": f"Bearer {token}"},
    ) as client:
        yield client


@pytest_asyncio.fixture()
async def user_http_client_with_user_id(
    http_client: AsyncClient,
) -> AsyncGenerator[tuple[AsyncClient, str], None]:
    """
    Like user_http_client but also yields the user's ID so tests can
    reference their own resources.

    The user ID is extracted from the registration response.
    """
    email = f"e2e-user-{uuid.uuid4().hex[:8]}@example.com"
    password = "ValidPass1!"

    # Register the user and extract ID
    register_resp = await http_client.post(
        "/users/",
        json={
            "email": email,
            "password": password,
        },
    )
    assert register_resp.status_code == 201, (
        f"Registration failed: {register_resp.text}"
    )
    user_id = register_resp.json()["id"]

    # Login to get token
    login_resp = await http_client.post(
        "/auth/login",
        json={
            "email": email,
            "password": password,
        },
    )
    assert login_resp.status_code == 200, f"Login failed: {login_resp.text}"
    token = login_resp.json()["access_token"]

    # Create authenticated client
    async with AsyncClient(
        base_url=_BASE_URL,
        headers={"Authorization": f"Bearer {token}"},
    ) as client:
        yield client, user_id


# ---------------------------------------------------------------------------
# Helper: Create test data
# ---------------------------------------------------------------------------


async def create_merchant_via_api(
    admin_client: AsyncClient,
    *,
    name: str | None = None,
    cashback_percentage: float = 5.0,
    active: bool = True,
) -> dict[str, Any]:
    """Create a merchant via API and return its details (including ID)."""
    merchant_name = name or f"E2E Merchant {uuid.uuid4().hex[:6]}"
    resp = await admin_client.post(
        "/merchants/",
        json={
            "name": merchant_name,
            "default_cashback_percentage": cashback_percentage,
            "active": active,
        },
    )
    assert resp.status_code == 201, f"Merchant creation failed: {resp.text}"
    return resp.json()


async def create_offer_via_api(
    admin_client: AsyncClient,
    merchant_id: str,
    *,
    percentage: float = 5.0,
    monthly_cap: float = 100.0,
) -> dict[str, Any]:
    """Create an offer via API and return its details (including ID)."""
    from datetime import date, timedelta

    today = date.today()
    future = today + timedelta(days=30)

    resp = await admin_client.post(
        "/offers/",
        json={
            "merchant_id": merchant_id,
            "cashback_type": "percent",
            "cashback_value": percentage,
            "monthly_cap": monthly_cap,
            "start_date": str(today),
            "end_date": str(future),
        },
    )
    assert resp.status_code == 201, f"Offer creation failed: {resp.text}"
    return resp.json()


async def activate_merchant_via_api(
    admin_client: AsyncClient,
    merchant_id: str,
) -> dict[str, Any]:
    """Activate a merchant via API."""
    resp = await admin_client.patch(
        f"/merchants/{merchant_id}/status",
        json={"status": "active"},
    )
    assert resp.status_code == 200, f"Merchant activation failed: {resp.text}"
    return resp.json()


async def deactivate_merchant_via_api(
    admin_client: AsyncClient,
    merchant_id: str,
) -> dict[str, Any]:
    """Deactivate a merchant via API."""
    resp = await admin_client.patch(
        f"/merchants/{merchant_id}/status",
        json={"status": "inactive"},
    )
    assert resp.status_code == 200, f"Merchant deactivation failed: {resp.text}"
    return resp.json()


async def activate_offer_via_api(
    admin_client: AsyncClient,
    offer_id: str,
) -> dict[str, Any]:
    """Activate an offer via API."""
    resp = await admin_client.patch(
        f"/offers/{offer_id}/status",
        json={"status": "active"},
    )
    assert resp.status_code == 200, f"Offer activation failed: {resp.text}"
    return resp.json()


async def deactivate_offer_via_api(
    admin_client: AsyncClient,
    offer_id: str,
) -> dict[str, Any]:
    """Deactivate an offer via API."""
    resp = await admin_client.patch(
        f"/offers/{offer_id}/status",
        json={"status": "inactive"},
    )
    assert resp.status_code == 200, f"Offer deactivation failed: {resp.text}"
    return resp.json()


# ---------------------------------------------------------------------------
# Re-export helpers for use in test files
# ---------------------------------------------------------------------------

__all__ = [
    "http_client",
    "user_http_client",
    "admin_http_client",
    "user_http_client_with_user_id",
    "create_merchant_via_api",
    "create_offer_via_api",
    "activate_merchant_via_api",
    "deactivate_merchant_via_api",
    "activate_offer_via_api",
    "deactivate_offer_via_api",
]
