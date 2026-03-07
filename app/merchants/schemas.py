from typing import Literal
from uuid import UUID

from pydantic import BaseModel


class MerchantSchemaBase(BaseModel):
    name: str
    # TODO: Add validation to ensure this is a valid percentage (e.g., between 0 and 100)
    default_cashback_percentage: float
    active: bool = True


class MerchantOut(MerchantSchemaBase):
    id: UUID

    model_config = {"from_attributes": True}


class MerchantCreate(MerchantSchemaBase):
    pass


class PaginatedMerchantsOut(BaseModel):
    items: list[MerchantOut]
    total: int
    page: int
    page_size: int


class MerchantStatusUpdate(BaseModel):
    status: Literal["active", "inactive"]


class MerchantStatusOut(BaseModel):
    id: UUID
    status: str
