"""Integration tests for POST /api/v1/auth/login."""

from typing import Any

import pytest
from fastapi import status
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.integration.conftest import create_user

pytestmark = pytest.mark.asyncio


def _payload() -> dict[str, Any]:
    return {"email": "login-user@example.com", "password": "ValidPass1!"}


async def test_login_returns_200_with_token_on_success(
    http_client: AsyncClient,
    db: AsyncSession,
) -> None:
    # Arrange
    await create_user(db, **_payload())

    # Act
    response = await http_client.post("/api/v1/auth/login", json=_payload())

    # Assert
    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    access_token = body["access_token"]
    assert access_token
    assert body["token_type"] == "bearer"
    assert len(access_token) > 10


async def test_login_returns_401_on_wrong_password(
    http_client: AsyncClient,
    db: AsyncSession,
) -> None:
    # Arrange
    email = "wrong-pw@example.com"
    await create_user(db, email=email, password="ValidPass1!")

    # Act
    response = await http_client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "WrongPass9!"},
    )

    # Assert
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    body = response.json()
    assert body["error"]["code"] == "INVALID_CREDENTIALS"


async def test_login_returns_401_on_unknown_email(
    http_client: AsyncClient,
) -> None:
    # Act
    response = await http_client.post(
        "/api/v1/auth/login",
        json={"email": "nobody@example.com", "password": "ValidPass1!"},
    )

    # Assert
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    body = response.json()
    assert body["error"]["code"] == "INVALID_CREDENTIALS"
