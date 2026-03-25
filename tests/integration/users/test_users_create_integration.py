"""Integration tests for POST /api/v1/users/."""

from typing import Any

import pytest
from fastapi import status
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.integration.conftest import create_user

pytestmark = pytest.mark.asyncio


def _payload() -> dict[str, Any]:
    return {"email": "newuser@example.com", "password": "ValidPass1!"}


async def test_create_user_returns_201_on_success(
    http_client: AsyncClient,
) -> None:
    # Act
    response = await http_client.post("/api/v1/users/", json=_payload())

    # Assert
    assert response.status_code == status.HTTP_201_CREATED
    body = response.json()
    assert body["email"] == "newuser@example.com"
    assert body["active"] is True
    assert body["role"] == "user"
    assert body["created_at"]


async def test_create_user_returns_409_on_duplicate_email(
    http_client: AsyncClient,
    db: AsyncSession,
) -> None:
    # Arrange: pre-create a user with the same email
    email = "duplicate@example.com"
    await create_user(db, email=email)

    # Act
    response = await http_client.post(
        "/api/v1/users/",
        json={"email": email, "password": "ValidPass1!"},
    )

    # Assert
    assert response.status_code == status.HTTP_409_CONFLICT
    body = response.json()
    assert body["error"]["code"] == "EMAIL_ALREADY_REGISTERED"
    assert body["error"]["details"]["email"] == email


async def test_create_user_returns_400_on_weak_password(
    http_client: AsyncClient,
) -> None:
    # Act: "weak" is too short and missing uppercase, digit, special char
    response = await http_client.post(
        "/api/v1/users/",
        json={"email": "weakpass@example.com", "password": "weak"},
    )

    # Assert
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    body = response.json()
    assert body["error"]["code"] == "PASSWORD_NOT_COMPLEX_ENOUGH"
    assert len(body["error"]["details"]["violations"]) > 0
