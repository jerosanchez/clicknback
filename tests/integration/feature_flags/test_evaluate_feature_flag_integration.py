"""Integration tests for GET /api/v1/feature-flags/{key}/evaluate."""

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
# GET /api/v1/feature-flags/{key}/evaluate — Happy paths
# ──────────────────────────────────────────────────────────────────────────────


async def test_evaluate_feature_flag_returns_enabled_on_global_flag(
    admin_http_client: AsyncClient,
    db: AsyncSession,
) -> None:
    # Arrange
    key = f"test_flag_{uuid.uuid4().hex[:8]}"
    await _seed_flag(db, key=key, enabled=True, scope_type="global")

    # Act
    response = await admin_http_client.get(f"/api/v1/feature-flags/{key}/evaluate")

    # Assert
    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert body["key"] == key
    assert body["enabled"] is True


async def test_evaluate_feature_flag_returns_disabled_on_global_flag(
    admin_http_client: AsyncClient,
    db: AsyncSession,
) -> None:
    # Arrange
    key = f"test_flag_{uuid.uuid4().hex[:8]}"
    await _seed_flag(db, key=key, enabled=False, scope_type="global")

    # Act
    response = await admin_http_client.get(f"/api/v1/feature-flags/{key}/evaluate")

    # Assert
    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert body["key"] == key
    assert body["enabled"] is False


async def test_evaluate_feature_flag_returns_merchant_scoped_override(
    admin_http_client: AsyncClient,
    db: AsyncSession,
) -> None:
    # Arrange
    key = f"test_flag_{uuid.uuid4().hex[:8]}"
    merchant_id = str(uuid.uuid4())
    # Global flag is disabled
    await _seed_flag(db, key=key, enabled=False, scope_type="global")
    # But merchant-scoped override is enabled
    await _seed_flag(
        db, key=key, enabled=True, scope_type="merchant", scope_id=merchant_id
    )

    # Act
    response = await admin_http_client.get(
        f"/api/v1/feature-flags/{key}/evaluate?scope_type=merchant&scope_id={merchant_id}"
    )

    # Assert
    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert body["key"] == key
    assert body["enabled"] is True


async def test_evaluate_feature_flag_falls_back_to_global_when_scoped_missing(
    admin_http_client: AsyncClient,
    db: AsyncSession,
) -> None:
    # Arrange
    key = f"test_flag_{uuid.uuid4().hex[:8]}"
    merchant_id = str(uuid.uuid4())
    # Only global flag exists
    await _seed_flag(db, key=key, enabled=False, scope_type="global")

    # Act
    response = await admin_http_client.get(
        f"/api/v1/feature-flags/{key}/evaluate?scope_type=merchant&scope_id={merchant_id}"
    )

    # Assert
    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert body["key"] == key
    assert body["enabled"] is False  # Falls back to disabled global


async def test_evaluate_feature_flag_returns_fail_open_default_when_no_flag_exists(
    admin_http_client: AsyncClient,
) -> None:
    # Arrange — key that has no flag record anywhere
    key = f"new_flag_{uuid.uuid4().hex[:8]}"

    # Act
    response = await admin_http_client.get(f"/api/v1/feature-flags/{key}/evaluate")

    # Assert
    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert body["key"] == key
    assert body["enabled"] is True  # Fail-open default


async def test_evaluate_feature_flag_with_user_scope(
    admin_http_client: AsyncClient,
    db: AsyncSession,
) -> None:
    # Arrange
    key = f"test_flag_{uuid.uuid4().hex[:8]}"
    user_id = str(uuid.uuid4())
    await _seed_flag(db, key=key, enabled=True, scope_type="user", scope_id=user_id)

    # Act
    response = await admin_http_client.get(
        f"/api/v1/feature-flags/{key}/evaluate?scope_type=user&scope_id={user_id}"
    )

    # Assert
    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert body["key"] == key
    assert body["enabled"] is True


# ──────────────────────────────────────────────────────────────────────────────
# GET /api/v1/feature-flags/{key}/evaluate — Failure paths
# ──────────────────────────────────────────────────────────────────────────────


async def test_evaluate_feature_flag_returns_401_on_unauthenticated(
    http_client: AsyncClient,
) -> None:
    # Act
    response = await http_client.get("/api/v1/feature-flags/some_flag/evaluate")

    # Assert
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


async def test_evaluate_feature_flag_returns_401_on_non_admin(
    user_http_client: AsyncClient,
) -> None:
    # Act
    response = await user_http_client.get("/api/v1/feature-flags/some_flag/evaluate")

    # Assert — the admin-only guard rejects non-admin tokens with 401
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


async def test_evaluate_feature_flag_returns_422_on_missing_scope_id_for_merchant(
    admin_http_client: AsyncClient,
) -> None:
    # Act
    response = await admin_http_client.get(
        "/api/v1/feature-flags/some_flag/evaluate?scope_type=merchant"
    )

    # Assert
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    body = response.json()
    assert body["error"]["code"] == "FEATURE_FLAG_SCOPE_ID_REQUIRED"
    assert body["error"]["details"]["scope_type"] == "merchant"


async def test_evaluate_feature_flag_returns_422_on_missing_scope_id_for_user(
    admin_http_client: AsyncClient,
) -> None:
    # Act
    response = await admin_http_client.get(
        "/api/v1/feature-flags/some_flag/evaluate?scope_type=user"
    )

    # Assert
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    body = response.json()
    assert body["error"]["code"] == "FEATURE_FLAG_SCOPE_ID_REQUIRED"
    assert body["error"]["details"]["scope_type"] == "user"
