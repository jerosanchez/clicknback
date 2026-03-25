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
# JwtOAuth2TokenProvider
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
    token_provider.ttl_in_minutes = expired_ttl
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
