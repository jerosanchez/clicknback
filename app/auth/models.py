from dataclasses import dataclass


@dataclass(frozen=True)
class User:
    id: str
    email: str
    hashed_password: str


@dataclass(frozen=True)
class Token:
    access_token: str
    token_type: str


@dataclass(frozen=True)
class TokenPayload:
    user_id: str | None = None
