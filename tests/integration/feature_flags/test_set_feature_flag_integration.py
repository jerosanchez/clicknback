"""Integration tests for PUT /api/v1/feature-flags/{key}."""

import uuid

import pytest
from fastapi import status
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.feature_flags.models import FeatureFlag

pytestmark = pytest.mark.asyncio


# ──────────────────────────────────────────────────────────────────────────────
# Seeding helpers
# ──────────────────────────────────────────────────────────────────────────────


async def _seed_flag(
    db: AsyncSession,
    *,
    key: str,
    enabled: bool = True,
    scope_type: str = "global",
    scope_id: str | None = None,
) -> FeatureFlag:
    """Insert a FeatureFlag row and flush into the test transaction."""
    flag = FeatureFlag(
        key=key,
        enabled=enabled,
        scope_type=scope_type,
        scope_id=scope_id,
    )
    db.add(flag)
    await db.flush()
    return flag


# ──────────────────────────────────────────────────────────────────────────────
# PUT /api/v1/feature-flags/{key} — Happy paths
# ──────────────────────────────────────────────────────────────────────────────


async def test_set_feature_flag_creates_global_flag(
    admin_http_client: AsyncClient,
) -> None:
    # Arrange — unique key so it does not conflict with other tests
    key = f"test_flag_{uuid.uuid4().hex[:8]}"

    # Act
    response = await admin_http_client.put(
        f"/api/v1/feature-flags/{key}",
        json={"enabled": False},
    )

    # Assert
    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert body["key"] == key
    assert body["enabled"] is False
    assert body["scope_type"] == "global"
    assert body["scope_id"] is None
    assert body["id"] is not None
    assert body["created_at"] is not None
    assert body["updated_at"] is not None


async def test_set_feature_flag_creates_merchant_scoped_flag(
    admin_http_client: AsyncClient,
) -> None:
    # Arrange
    key = f"test_flag_{uuid.uuid4().hex[:8]}"
    merchant_id = str(uuid.uuid4())

    # Act
    response = await admin_http_client.put(
        f"/api/v1/feature-flags/{key}",
        json={
            "enabled": True,
            "scope_type": "merchant",
            "scope_id": merchant_id,
            "description": "Scoped to one merchant",
        },
    )

    # Assert
    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert body["key"] == key
    assert body["scope_type"] == "merchant"
    assert body["scope_id"] == merchant_id
    assert body["description"] == "Scoped to one merchant"


async def test_set_feature_flag_updates_existing_flag(
    admin_http_client: AsyncClient,
    db: AsyncSession,
) -> None:
    # Arrange — seed an existing flag, then update it via the endpoint
    key = f"test_flag_{uuid.uuid4().hex[:8]}"
    await _seed_flag(db, key=key, enabled=True)

    # Act
    response = await admin_http_client.put(
        f"/api/v1/feature-flags/{key}",
        json={"enabled": False, "description": "Updated"},
    )

    # Assert
    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert body["key"] == key
    assert body["enabled"] is False
    assert body["description"] == "Updated"


async def test_set_feature_flag_upsert_is_idempotent(
    admin_http_client: AsyncClient,
) -> None:
    # Arrange — call twice with the same key/scope; both should succeed
    key = f"test_flag_{uuid.uuid4().hex[:8]}"
    payload = {"enabled": True}

    # Act
    first = await admin_http_client.put(f"/api/v1/feature-flags/{key}", json=payload)
    second = await admin_http_client.put(f"/api/v1/feature-flags/{key}", json=payload)

    # Assert — both return 200 and the same key
    assert first.status_code == status.HTTP_200_OK
    assert second.status_code == status.HTTP_200_OK
    assert first.json()["key"] == second.json()["key"]


# ──────────────────────────────────────────────────────────────────────────────
# PUT /api/v1/feature-flags/{key} — Failure modes
# ──────────────────────────────────────────────────────────────────────────────


async def test_set_feature_flag_returns_401_for_unauthenticated(
    http_client: AsyncClient,
) -> None:
    # Act
    response = await http_client.put(
        "/api/v1/feature-flags/some_flag",
        json={"enabled": True},
    )

    # Assert
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


async def test_set_feature_flag_returns_403_for_regular_user(
    user_http_client: AsyncClient,
) -> None:
    # Act
    response = await user_http_client.put(
        "/api/v1/feature-flags/some_flag",
        json={"enabled": True},
    )

    # Assert — the admin-only guard rejects non-admin tokens with 401
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


async def test_set_feature_flag_returns_422_for_invalid_key_format(
    admin_http_client: AsyncClient,
) -> None:
    # Arrange — key contains uppercase letters (not snake_case)
    invalid_key = "PurchaseConfirmationJob"

    # Act
    response = await admin_http_client.put(
        f"/api/v1/feature-flags/{invalid_key}",
        json={"enabled": False},
    )

    # Assert
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    body = response.json()
    assert body["error"]["code"] == "VALIDATION_ERROR"


async def test_set_feature_flag_returns_422_for_merchant_scope_without_scope_id(
    admin_http_client: AsyncClient,
) -> None:
    # Act
    response = await admin_http_client.put(
        "/api/v1/feature-flags/fraud_check",
        json={"enabled": False, "scope_type": "merchant"},
    )

    # Assert
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    body = response.json()
    assert body["error"]["code"] == "FEATURE_FLAG_SCOPE_ID_REQUIRED"
    assert body["error"]["details"]["scope_type"] == "merchant"
