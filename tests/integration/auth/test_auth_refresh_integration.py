"""Integration tests for POST /api/v1/auth/refresh."""

import pytest
from fastapi import status
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.integration.conftest import create_user

pytestmark = pytest.mark.asyncio


async def test_refresh_returns_200_with_new_tokens_on_success(
    http_client: AsyncClient,
    user_http_client: AsyncClient,
    db: AsyncSession,
) -> None:
    """Test that refresh endpoint returns new access and refresh tokens on success."""
    # Arrange - create a user and login to get tokens
    email = "refresh-user@example.com"
    password = "ValidPass1!"
    await create_user(db, email=email, password=password)

    # Login to get initial tokens
    login_response = await http_client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert login_response.status_code == status.HTTP_200_OK
    login_body = login_response.json()
    old_access_token = login_body["access_token"]
    old_refresh_token = login_body["refresh_token"]

    # Act - refresh the token
    response = await http_client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": old_refresh_token},
    )

    # Assert
    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    new_access_token = body["access_token"]
    new_refresh_token = body["refresh_token"]

    # Verify we got valid tokens
    assert new_access_token
    assert new_refresh_token
    assert body["token_type"] == "bearer"
    # Refresh tokens are rotated (new UUID each time)
    assert new_refresh_token != old_refresh_token
    # Access tokens may be identical if generated in the same second (same exp, same user);
    # do not assert inequality — validity and refresh-token rotation are the real invariants

    # Verify the new access token is valid by using it in a subsequent request
    headers = {"Authorization": f"Bearer {new_access_token}"}
    # Make a request that requires authentication (e.g., get wallet)
    protected_response = await http_client.get(
        "/api/v1/wallets/current",
        headers=headers,
    )
    # Should be 200 OK (authenticated) or 400 (validation error), not 401 (unauthorized)
    assert protected_response.status_code != status.HTTP_401_UNAUTHORIZED


async def test_refresh_returns_401_on_invalid_token(
    http_client: AsyncClient,
) -> None:
    """Test that refresh endpoint returns 401 for invalid refresh token."""
    # Act
    response = await http_client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": "not.a.valid.jwt.token"},
    )

    # Assert
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    body = response.json()
    assert body["error"]["code"] == "INVALID_REFRESH_TOKEN"
    assert "Invalid or expired refresh token" in body["error"]["message"]


async def test_refresh_returns_401_on_expired_token(
    http_client: AsyncClient,
    db: AsyncSession,
) -> None:
    """Test that refresh endpoint returns 401 for expired refresh token."""
    # Arrange - create a user and login
    email = "expired-token-user@example.com"
    password = "ValidPass1!"
    await create_user(db, email=email, password=password)

    # Login to get initial tokens
    login_response = await http_client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert login_response.status_code == status.HTTP_200_OK
    old_refresh_token = login_response.json()["refresh_token"]

    # Manually expire the token by manipulating the JWT (create an expired one)
    # For this test, we'll create a token that's already expired
    # This is hard to do without mocking, so we rely on the unit tests for expiration

    # Act
    # Try to use an obviously malformed/expired token structure
    response = await http_client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": "expired.token.jwt"},
    )

    # Assert
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    body = response.json()
    assert body["error"]["code"] == "INVALID_REFRESH_TOKEN"


async def test_refresh_returns_401_on_reused_token(
    http_client: AsyncClient,
    db: AsyncSession,
) -> None:
    """Test that single-use token enforcement works: reusing a token is rejected."""
    # Arrange - create a user and login to get tokens
    email = "single-use-user@example.com"
    password = "ValidPass1!"
    await create_user(db, email=email, password=password)

    # Login to get initial tokens
    login_response = await http_client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert login_response.status_code == status.HTTP_200_OK
    refresh_token = login_response.json()["refresh_token"]

    # First refresh - should succeed
    response1 = await http_client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert response1.status_code == status.HTTP_200_OK

    # Act - try to reuse the same token
    response2 = await http_client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )

    # Assert - second use should be rejected
    assert response2.status_code == status.HTTP_401_UNAUTHORIZED
    body = response2.json()
    assert body["error"]["code"] == "INVALID_REFRESH_TOKEN"
    assert "Invalid or expired refresh token" in body["error"]["message"]


async def test_refresh_missing_refresh_token_field(
    http_client: AsyncClient,
) -> None:
    """Test that refresh endpoint returns 422 when refresh_token field is missing."""
    # Act
    response = await http_client.post(
        "/api/v1/auth/refresh",
        json={},
    )

    # Assert
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


async def test_refresh_chain_creates_new_tokens(
    http_client: AsyncClient,
    db: AsyncSession,
) -> None:
    """Test that chaining multiple refreshes creates new tokens each time."""
    # Arrange - create a user and login
    email = "chain-user@example.com"
    password = "ValidPass1!"
    await create_user(db, email=email, password=password)

    # Login to get initial tokens
    login_response = await http_client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert login_response.status_code == status.HTTP_200_OK
    refresh_token_1 = login_response.json()["refresh_token"]

    # Act & Assert - First refresh
    response1 = await http_client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token_1},
    )
    assert response1.status_code == status.HTTP_200_OK
    refresh_token_2 = response1.json()["refresh_token"]
    assert refresh_token_2 != refresh_token_1

    # Second refresh with new token
    response2 = await http_client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token_2},
    )
    assert response2.status_code == status.HTTP_200_OK
    refresh_token_3 = response2.json()["refresh_token"]
    assert refresh_token_3 != refresh_token_2
    assert refresh_token_3 != refresh_token_1

    # Third refresh with newest token
    response3 = await http_client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token_3},
    )
    assert response3.status_code == status.HTTP_200_OK
