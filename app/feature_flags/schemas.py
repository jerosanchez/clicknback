from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class FeatureFlagSet(BaseModel):
    enabled: bool
    scope_type: Literal["global", "merchant", "user"] = "global"
    scope_id: UUID | None = None
    description: str | None = None


class FeatureFlagOut(BaseModel):
    id: UUID
    key: str
    enabled: bool
    scope_type: str
    scope_id: UUID | None
    description: str | None
    created_at: datetime | None
    updated_at: datetime | None

    model_config = {"from_attributes": True}


class FeatureFlagKeyValidator(BaseModel):
    key: str = Field(..., min_length=1, max_length=100)

    @field_validator("key")
    @classmethod
    def key_must_be_snake_case(cls, v: str) -> str:
        import re

        if not re.fullmatch(r"[a-z][a-z0-9_]*", v):
            raise ValueError(
                "key must be lowercase snake_case (letters, digits, underscores; "
                "must start with a letter)."
            )
        return v
