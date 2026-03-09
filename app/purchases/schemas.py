from datetime import datetime
from decimal import Decimal
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class PurchaseStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    REVERSED = "reversed"


class PurchaseCreate(BaseModel):
    external_id: str = Field(
        ...,
        min_length=1,
        description="Unique identifier from the external system (idempotency key).",
    )
    user_id: UUID = Field(..., description="ID of the user making the purchase.")
    merchant_id: UUID = Field(..., description="ID of the merchant.")
    amount: Decimal = Field(
        ..., gt=0, description="Purchase amount. Must be a positive number."
    )

    currency: str = Field(
        ...,
        min_length=3,
        max_length=3,
        description="ISO 4217 currency code. Currently only EUR is accepted.",
    )

    @field_validator("amount")
    def amount_scale_must_not_exceed_2(cls, value: Decimal):
        exponent = value.as_tuple().exponent
        if isinstance(exponent, int):
            decimal_places = -exponent if exponent < 0 else 0
            if decimal_places > 2:
                raise ValueError("Amount must have at most 2 decimal places")
        else:
            raise ValueError("Amount must be a finite decimal number")
        return value


class PurchaseOut(BaseModel):
    model_config = {"from_attributes": True}

    id: str
    status: str
    cashback_amount: Decimal = Decimal("0")


class PurchaseAdminOut(BaseModel):
    model_config = {"from_attributes": True}

    id: str
    external_id: str
    user_id: str
    merchant_id: str
    offer_id: str | None
    amount: Decimal
    currency: str
    status: PurchaseStatus
    created_at: datetime


class PaginatedPurchaseOut(BaseModel):
    items: list[PurchaseAdminOut]
    total: int
    page: int
    page_size: int
