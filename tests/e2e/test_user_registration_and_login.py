"""End-to-end tests for user registration and login flow."""

import uuid

import pytest
from fastapi import status
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


async def test_user_register_and_login_flow(http_client: AsyncClient) -> None:
    """
    E2E: User registration → login → receive valid JWT.

    Validates the complete authentication flow: anonymous user registers,
    receives user ID and email confirmation, then logs in to get a token.
    """
    # Arrange
    email = f"e2e-test-{uuid.uuid4().hex[:8]}@example.com"
    password = "ValidPass1!"

    # Act 1: Register (anonymous → user with ID)
    register_response = await http_client.post(
        "/users/",
        json={
            "email": email,
            "password": password,
        },
    )

    # Assert registration
    assert register_response.status_code == status.HTTP_201_CREATED
    register_body = register_response.json()
    user_id = register_body["id"]
    assert user_id is not None
    assert register_body["email"] == email
    assert register_body["role"] == "user"
    assert register_body["active"] is True
    assert "created_at" in register_body

    # Act 2: Login with registered credentials
    login_response = await http_client.post(
        "/auth/login",
        json={
            "email": email,
            "password": password,
        },
    )

    # Assert login
    assert login_response.status_code == status.HTTP_200_OK
    login_body = login_response.json()
    assert "access_token" in login_body
    assert "refresh_token" in login_body
    assert login_body["token_type"] == "bearer"
    access_token = login_body["access_token"]
    refresh_token = login_body["refresh_token"]
    assert isinstance(access_token, str)
    assert len(access_token) > 10  # JWT should be non-trivial length

    # Act 3: Refresh the token
    refresh_response = await http_client.post(
        "/auth/refresh",
        json={"refresh_token": refresh_token},
    )

    # Assert refresh issued new tokens
    assert refresh_response.status_code == status.HTTP_200_OK
    refresh_body = refresh_response.json()
    new_access_token = refresh_body["access_token"]
    new_refresh_token = refresh_body["refresh_token"]
    assert new_access_token
    assert new_refresh_token
    assert refresh_body["token_type"] == "bearer"
    # Refresh tokens are rotated — new UUID each time
    assert new_refresh_token != refresh_token

    # Act 4: Use the new access token on a protected endpoint
    authenticated_response = await http_client.get(
        "/offers/active",
        headers={"Authorization": f"Bearer {new_access_token}"},
    )

    # Assert new token is accepted (not 401)
    assert authenticated_response.status_code == status.HTTP_200_OK

    # Act 5: Original refresh token must be rejected (single-use)
    reuse_response = await http_client.post(
        "/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert reuse_response.status_code == status.HTTP_401_UNAUTHORIZED


async def test_user_register_fails_on_duplicate_email(http_client: AsyncClient) -> None:
    """
    E2E: Attempting to register with a duplicate email fails with 409.

    Validates idempotency and email uniqueness constraint.
    """
    # Arrange
    email = f"e2e-dup-{uuid.uuid4().hex[:8]}@example.com"
    password = "ValidPass1!"

    # Act 1: Register first user
    first_response = await http_client.post(
        "/users/",
        json={
            "email": email,
            "password": password,
        },
    )
    assert first_response.status_code == status.HTTP_201_CREATED

    # Act 2: Attempt to register with same email
    duplicate_response = await http_client.post(
        "/users/",
        json={
            "email": email,
            "password": password,
        },
    )

    # Assert
    assert duplicate_response.status_code == status.HTTP_409_CONFLICT
    error_body = duplicate_response.json()
    assert error_body["error"]["code"] == "EMAIL_ALREADY_REGISTERED"
    assert email in error_body["error"]["message"]


async def test_user_login_fails_on_wrong_password(http_client: AsyncClient) -> None:
    """
    E2E: Login with wrong password returns 401.

    Validates credential verification and rejection of invalid attempts.
    """
    # Arrange
    email = f"e2e-pwd-{uuid.uuid4().hex[:8]}@example.com"
    correct_password = "ValidPass1!"
    wrong_password = "WrongPass9!"

    # Act 1: Register user
    register_response = await http_client.post(
        "/users/",
        json={
            "email": email,
            "password": correct_password,
        },
    )
    assert register_response.status_code == status.HTTP_201_CREATED

    # Act 2: Attempt login with wrong password
    login_response = await http_client.post(
        "/auth/login",
        json={
            "email": email,
            "password": wrong_password,
        },
    )

    # Assert
    assert login_response.status_code == status.HTTP_401_UNAUTHORIZED
    error_body = login_response.json()
    assert error_body["error"]["code"] == "INVALID_CREDENTIALS"


async def test_user_login_fails_on_unknown_email(http_client: AsyncClient) -> None:
    """
    E2E: Login with unknown email returns 401.

    Validates that login rejects non-existent accounts.
    """
    # Act
    login_response = await http_client.post(
        "/auth/login",
        json={
            "email": f"nobody-{uuid.uuid4().hex[:8]}@example.com",
            "password": "SomePass1!",
        },
    )

    # Assert
    assert login_response.status_code == status.HTTP_401_UNAUTHORIZED
    error_body = login_response.json()
    assert error_body["error"]["code"] == "INVALID_CREDENTIALS"


async def test_user_register_fails_on_weak_password(http_client: AsyncClient) -> None:
    """
    E2E: Registration with weak password returns 400.

    Validates password complexity requirements (domain policy violation).
    """
    # Act
    register_response = await http_client.post(
        "/users/",
        json={
            "email": f"e2e-weak-{uuid.uuid4().hex[:8]}@example.com",
            "password": "weak",  # Too short, no special chars, etc.
        },
    )

    # Assert
    assert register_response.status_code == status.HTTP_400_BAD_REQUEST
    error_body = register_response.json()
    assert error_body["error"]["code"] == "PASSWORD_NOT_COMPLEX_ENOUGH"


async def test_authenticated_request_with_valid_token(
    user_http_client: AsyncClient,
) -> None:
    """
    E2E: Valid JWT token is accepted by authenticated endpoints.

    Validates that the token generated by login is accepted by the API.
    """
    # Note: user_http_client is already authenticated via the fixture.
    # We test that it works by making a request to ANY authenticated endpoint.
    # For now, we'll use GET /offers/active which requires authentication.

    # Act
    response = await user_http_client.get("/offers/active")

    # Assert: should get a 200 (even if empty list), not 401/403
    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert "data" in body
    assert isinstance(body["data"], list)
