from abc import ABC, abstractmethod
from dataclasses import asdict
from datetime import datetime, timedelta, timezone

from jose import jwt

from app.core.config import settings

from .models import TokenPayload


class OAuth2TokenProviderABC(ABC):
    @staticmethod
    @abstractmethod
    def create_access_token(payload: TokenPayload) -> str:
        pass


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
