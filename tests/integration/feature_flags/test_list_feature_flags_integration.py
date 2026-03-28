"""Integration tests for GET /api/v1/feature-flags."""

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
    description: str | None = None,
) -> FeatureFlag:
    """Insert a FeatureFlag row and flush into the test transaction."""
    flag = FeatureFlag(
        key=key,
        enabled=enabled,
        scope_type=scope_type,
        scope_id=scope_id,
        description=description,
    )
    db.add(flag)
    await db.flush()
    return flag


# ──────────────────────────────────────────────────────────────────────────────
# GET /api/v1/feature-flags — Happy paths
# ──────────────────────────────────────────────────────────────────────────────


async def test_list_feature_flags_returns_all_flags(
    admin_http_client: AsyncClient,
    db: AsyncSession,
) -> None:
    # Arrange — seed multiple flags
    key1 = f"flag_{uuid.uuid4().hex[:8]}"
    key2 = f"flag_{uuid.uuid4().hex[:8]}"
    await _seed_flag(db, key=key1, enabled=True)
    await _seed_flag(db, key=key2, enabled=False)

    # Act
    response = await admin_http_client.get("/api/v1/feature-flags")

    # Assert
    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert body["total"] >= 2
    assert len(body["items"]) >= 2
    assert isinstance(body["items"], list)
    # Verify structure of each item
    for item in body["items"]:
        assert "id" in item
        assert "key" in item
        assert "enabled" in item
        assert "scope_type" in item
        assert "scope_id" in item
        assert "description" in item
        assert "created_at" in item
        assert "updated_at" in item


async def test_list_feature_flags_filters_by_key(
    admin_http_client: AsyncClient,
    db: AsyncSession,
) -> None:
    # Arrange — seed flags with different keys
    key_to_find = f"flag_{uuid.uuid4().hex[:8]}"
    key_other = f"flag_{uuid.uuid4().hex[:8]}"
    await _seed_flag(db, key=key_to_find, enabled=True)
    await _seed_flag(db, key=key_other, enabled=False)

    # Act
    response = await admin_http_client.get(f"/api/v1/feature-flags?key={key_to_find}")

    # Assert
    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert body["total"] == 1
    assert len(body["items"]) == 1
    assert body["items"][0]["key"] == key_to_find


async def test_list_feature_flags_filters_by_scope_type(
    admin_http_client: AsyncClient,
    db: AsyncSession,
) -> None:
    # Arrange — seed both global and merchant-scoped flags
    key1 = f"flag_{uuid.uuid4().hex[:8]}"
    key2 = f"flag_{uuid.uuid4().hex[:8]}"
    merchant_id = str(uuid.uuid4())
    await _seed_flag(db, key=key1, enabled=True, scope_type="global")
    await _seed_flag(
        db, key=key2, enabled=False, scope_type="merchant", scope_id=merchant_id
    )

    # Act
    response = await admin_http_client.get("/api/v1/feature-flags?scope_type=merchant")

    # Assert
    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert body["total"] >= 1
    # All items should have scope_type "merchant"
    for item in body["items"]:
        assert item["scope_type"] == "merchant"


async def test_list_feature_flags_filters_by_scope_id(
    admin_http_client: AsyncClient,
    db: AsyncSession,
) -> None:
    # Arrange
    merchant_id = str(uuid.uuid4())
    key1 = f"flag_{uuid.uuid4().hex[:8]}"
    key2 = f"flag_{uuid.uuid4().hex[:8]}"
    await _seed_flag(
        db, key=key1, enabled=True, scope_type="merchant", scope_id=merchant_id
    )
    # Seed another with a different merchant
    other_merchant = str(uuid.uuid4())
    await _seed_flag(
        db, key=key2, enabled=False, scope_type="merchant", scope_id=other_merchant
    )

    # Act
    response = await admin_http_client.get(
        f"/api/v1/feature-flags?scope_id={merchant_id}"
    )

    # Assert
    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["scope_id"] == merchant_id


async def test_list_feature_flags_filters_by_combined_key_and_scope_type(
    admin_http_client: AsyncClient,
    db: AsyncSession,
) -> None:
    # Arrange
    key_to_find = f"flag_{uuid.uuid4().hex[:8]}"
    merchant_id = str(uuid.uuid4())
    # Create global version
    await _seed_flag(db, key=key_to_find, enabled=True, scope_type="global")
    # Create merchant-scoped version
    await _seed_flag(
        db,
        key=key_to_find,
        enabled=False,
        scope_type="merchant",
        scope_id=merchant_id,
    )

    # Act — filter for merchant scope only
    response = await admin_http_client.get(
        f"/api/v1/feature-flags?key={key_to_find}&scope_type=merchant"
    )

    # Assert
    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["key"] == key_to_find
    assert body["items"][0]["scope_type"] == "merchant"


async def test_list_feature_flags_returns_empty_for_nonexistent_key(
    admin_http_client: AsyncClient,
) -> None:
    # Act
    response = await admin_http_client.get(
        "/api/v1/feature-flags?key=definitely_does_not_exist_xyz"
    )

    # Assert
    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert body["total"] == 0
    assert body["items"] == []


async def test_list_feature_flags_response_structure_includes_timestamps(
    admin_http_client: AsyncClient,
    db: AsyncSession,
) -> None:
    # Arrange
    key = f"flag_{uuid.uuid4().hex[:8]}"
    await _seed_flag(db, key=key, enabled=True)

    # Act
    response = await admin_http_client.get(f"/api/v1/feature-flags?key={key}")

    # Assert
    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert len(body["items"]) >= 1
    item = body["items"][0]
    assert item["created_at"] is not None
    assert item["updated_at"] is not None


# ──────────────────────────────────────────────────────────────────────────────
# GET /api/v1/feature-flags — Failure modes
# ──────────────────────────────────────────────────────────────────────────────


async def test_list_feature_flags_returns_401_for_unauthenticated(
    http_client: AsyncClient,
) -> None:
    # Act
    response = await http_client.get("/api/v1/feature-flags")

    # Assert
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


async def test_list_feature_flags_returns_403_for_regular_user(
    user_http_client: AsyncClient,
) -> None:
    # Act
    response = await user_http_client.get("/api/v1/feature-flags")

    # Assert — the admin-only guard rejects non-admin tokens with 401
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
