import hashlib
import secrets
from abc import ABC, abstractmethod
from dataclasses import asdict
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from jose.exceptions import ExpiredSignatureError

from app.auth.exceptions import InternalJwtErrorException, InvalidTokenException
from app.auth.models import TokenPayload
from app.core.config import settings
from app.core.logging import logger


class OAuth2TokenProviderABC(ABC):
    @abstractmethod
    def create_access_token(self, payload: TokenPayload) -> str:
        pass

    @abstractmethod
    def verify_access_token(self, token: str) -> TokenPayload:
        pass

    @abstractmethod
    def create_refresh_token(self, user_id: str) -> str:
        """Generate a new refresh token."""
        pass

    @abstractmethod
    def verify_refresh_token(self, token: str) -> str:
        """Verify and extract user_id from refresh token."""
        pass

    @abstractmethod
    def hash_refresh_token(self, token: str) -> str:
        """Hash a refresh token for storage."""
        pass


# A JWT version of the OAuth2TokenProvider. If we later decide to switch to a different token strategy
# (e.g., opaque tokens with server-side storage), we can implement a new provider that adheres to the same interface
# without affecting the rest of the codebase.
class JwtOAuth2TokenProvider(OAuth2TokenProviderABC):

    def __init__(
        self,
        access_ttl_in_minutes: float = settings.oauth_access_token_ttl,
        refresh_ttl_in_minutes: float = settings.oauth_refresh_token_ttl,
    ):
        self.access_ttl_in_minutes = access_ttl_in_minutes
        self.refresh_ttl_in_minutes = refresh_ttl_in_minutes

    def create_access_token(self, payload: TokenPayload) -> str:
        payload_data = asdict(payload)
        expire_time = datetime.now(timezone.utc) + timedelta(
            minutes=self.access_ttl_in_minutes
        )
        payload_data["exp"] = expire_time
        payload_data["token_type"] = "access"

        return jwt.encode(
            payload_data, settings.oauth_hash_key, algorithm=settings.oauth_algorithm
        )

    def verify_access_token(self, token: str) -> TokenPayload:
        try:
            payload = jwt.decode(
                token,
                settings.oauth_hash_key,
                algorithms=[settings.oauth_algorithm],
            )

            user_id = payload.get("user_id")
            user_role = payload.get("user_role")
            if user_id is None or user_role is None:
                logger.warning(
                    "Token payload missing required fields.",
                    extra={"user_id": user_id or "-", "user_role": user_role or "-"},
                )
                raise InvalidTokenException()

            return TokenPayload(user_id=user_id, user_role=user_role)

        except ExpiredSignatureError:
            raise InvalidTokenException()

        except JWTError as e:
            logger.error("JWT processing error occurred.", extra={"error": str(e)})
            raise InternalJwtErrorException()

    def create_refresh_token(self, user_id: str) -> str:
        """Generate a new refresh token as a JWT."""
        expire_time = datetime.now(timezone.utc) + timedelta(
            minutes=self.refresh_ttl_in_minutes
        )
        payload = {
            "user_id": user_id,
            "exp": expire_time,
            "token_type": "refresh",
            "jti": secrets.token_urlsafe(32),  # Unique token ID for revocation/tracking
        }

        return jwt.encode(
            payload, settings.oauth_hash_key, algorithm=settings.oauth_algorithm
        )

    def verify_refresh_token(self, token: str) -> str:
        """Verify refresh token and return the user_id."""
        try:
            payload = jwt.decode(
                token,
                settings.oauth_hash_key,
                algorithms=[settings.oauth_algorithm],
            )

            user_id = payload.get("user_id")
            token_type = payload.get("token_type")

            if user_id is None or token_type != "refresh":
                logger.warning(
                    "Refresh token payload invalid.",
                    extra={"user_id": user_id or "-", "token_type": token_type or "-"},
                )
                raise InvalidTokenException()

            return user_id

        except ExpiredSignatureError:
            raise InvalidTokenException()
        except JWTError as e:
            logger.error("JWT processing error occurred.", extra={"error": str(e)})
            raise InternalJwtErrorException()

    def hash_refresh_token(self, token: str) -> str:
        """Hash refresh token for secure storage in database."""
        return hashlib.sha256(token.encode()).hexdigest()
