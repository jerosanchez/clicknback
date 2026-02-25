from uuid import UUID

from pydantic import BaseModel


class MerchantSchemaBase(BaseModel):
    name: str
    default_cashback_percentage: float
    active: bool = True


class MerchantOut(MerchantSchemaBase):
    id: UUID

    model_config = {"from_attributes": True}


class MerchantCreate(MerchantSchemaBase):
    pass
