from abc import ABC, abstractmethod
from dataclasses import asdict
from datetime import datetime, timedelta, timezone

from jose import jwt

from app.auth.models import TokenPayload
from app.core.config import settings


class OAuth2TokenProviderABC(ABC):
    @staticmethod
    @abstractmethod
    def create_access_token(payload: TokenPayload) -> str:
        pass


# A JWT version of the OAuth2TokenProvider. If we later decide to switch to a different token strategy
# (e.g., opaque tokens with server-side storage), we can implement a new provider that adheres to the same interface
# without affecting the rest of the codebase.
class JwtOAuth2TokenProvider(OAuth2TokenProviderABC):
    @staticmethod
    def create_access_token(payload: TokenPayload) -> str:
        payload_data = asdict(payload)
        expire_time = datetime.now(timezone.utc) + timedelta(
            minutes=settings.oauth_token_ttl
        )
        payload_data["exp"] = expire_time

        return jwt.encode(
            payload_data, settings.oauth_hash_key, algorithm=settings.oauth_algorithm
        )
