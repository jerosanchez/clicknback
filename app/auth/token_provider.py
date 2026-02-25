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


# A JWT version of the OAuth2TokenProvider. If we later decide to switch to a different token strategy
# (e.g., opaque tokens with server-side storage), we can implement a new provider that adheres to the same interface
# without affecting the rest of the codebase.
class JwtOAuth2TokenProvider(OAuth2TokenProviderABC):

    def __init__(self, ttl_in_minutes: float = settings.oauth_token_ttl):
        self.ttl_in_minutes = ttl_in_minutes

    def create_access_token(self, payload: TokenPayload) -> str:
        payload_data = asdict(payload)
        expire_time = datetime.now(timezone.utc) + timedelta(
            minutes=self.ttl_in_minutes
        )
        payload_data["exp"] = expire_time

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
