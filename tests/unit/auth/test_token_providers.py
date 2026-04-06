import pytest

from app.auth.exceptions import InternalJwtErrorException, InvalidTokenException
from app.auth.models import TokenPayload
from app.auth.token_provider import JwtOAuth2TokenProvider


# Fixtures
@pytest.fixture
def token_provider() -> JwtOAuth2TokenProvider:
    return JwtOAuth2TokenProvider()


@pytest.fixture
def token_payload() -> TokenPayload:
    return TokenPayload(
        user_id="fec7f1a1-eb68-4d6f-8ba4-47920cea39cb",
        user_role="user",
    )


# ──────────────────────────────────────────────────────────────────────────────
# JwtOAuth2TokenProvider - Access Token Methods
# ──────────────────────────────────────────────────────────────────────────────


def test_token_provider_returns_valid_payload_on_create_and_verify(
    token_provider: JwtOAuth2TokenProvider, token_payload: TokenPayload
) -> None:
    # Arrange

    # Act
    token = token_provider.create_access_token(token_payload)
    decoded = token_provider.verify_access_token(token)

    # Assert
    assert decoded.user_id == token_payload.user_id
    assert decoded.user_role == token_payload.user_role


def test_token_provider_raises_on_expired_token(
    token_provider: JwtOAuth2TokenProvider, token_payload: TokenPayload
) -> None:
    # Arrange
    expired_ttl = -10
    token_provider.access_ttl_in_minutes = expired_ttl
    token = token_provider.create_access_token(token_payload)

    # Act & Assert
    with pytest.raises(InvalidTokenException):
        token_provider.verify_access_token(token)


def test_token_provider_raises_on_invalid_token(
    token_provider: JwtOAuth2TokenProvider,
) -> None:
    # Arrange
    invalid_token = "not.a.valid.token"

    # Act & Assert
    with pytest.raises(InternalJwtErrorException):
        token_provider.verify_access_token(invalid_token)


# ──────────────────────────────────────────────────────────────────────────────
# JwtOAuth2TokenProvider - Refresh Token Methods
# ──────────────────────────────────────────────────────────────────────────────


def test_token_provider_creates_and_verifies_refresh_token(
    token_provider: JwtOAuth2TokenProvider,
) -> None:
    # Arrange
    user_id = "user-123"

    # Act
    token = token_provider.create_refresh_token(user_id)
    decoded_user_id = token_provider.verify_refresh_token(token)

    # Assert
    assert decoded_user_id == user_id
    assert isinstance(token, str)
    assert len(token) > 0


def test_token_provider_refresh_token_has_correct_token_type(
    token_provider: JwtOAuth2TokenProvider,
) -> None:
    # Arrange
    user_id = "user-123"

    # Act
    token = token_provider.create_refresh_token(user_id)
    # Verify by attempting to use it as a refresh token
    decoded_user_id = token_provider.verify_refresh_token(token)

    # Assert
    assert decoded_user_id == user_id


def test_token_provider_raises_on_expired_refresh_token(
    token_provider: JwtOAuth2TokenProvider,
) -> None:
    # Arrange
    user_id = "user-123"
    token_provider.refresh_ttl_in_minutes = -10  # Set to expired
    token = token_provider.create_refresh_token(user_id)

    # Act & Assert
    with pytest.raises(InvalidTokenException):
        token_provider.verify_refresh_token(token)


def test_token_provider_raises_on_invalid_refresh_token(
    token_provider: JwtOAuth2TokenProvider,
) -> None:
    # Arrange
    invalid_token = "not.a.valid.refresh.token"

    # Act & Assert
    with pytest.raises(InternalJwtErrorException):
        token_provider.verify_refresh_token(invalid_token)


def test_token_provider_hash_refresh_token_produces_consistent_hash(
    token_provider: JwtOAuth2TokenProvider,
) -> None:
    # Arrange
    token = "some_refresh_token"

    # Act
    hash1 = token_provider.hash_refresh_token(token)
    hash2 = token_provider.hash_refresh_token(token)

    # Assert
    assert hash1 == hash2
    assert len(hash1) == 64  # SHA256 produces 64 hex characters


def test_token_provider_hash_refresh_token_different_for_different_tokens(
    token_provider: JwtOAuth2TokenProvider,
) -> None:
    # Arrange
    token1 = "token_one"
    token2 = "token_two"

    # Act
    hash1 = token_provider.hash_refresh_token(token1)
    hash2 = token_provider.hash_refresh_token(token2)

    # Assert
    assert hash1 != hash2
