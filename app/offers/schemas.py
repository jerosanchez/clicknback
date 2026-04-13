from datetime import date
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, model_validator

from app.core.schemas import PaginationOut

# --- ENUMS ---


class OfferStatusEnum(str, Enum):
    active = "active"
    inactive = "inactive"


class CashbackTypeEnum(str, Enum):
    percent = "percent"
    fixed = "fixed"


# --- POST /offers/


class OfferCreate(BaseModel):
    merchant_id: UUID
    cashback_type: CashbackTypeEnum
    cashback_value: float
    start_date: date
    end_date: date
    monthly_cap: float


# --- GET /offers/


class OfferOut(BaseModel):
    id: UUID
    merchant_id: UUID
    cashback_type: CashbackTypeEnum
    cashback_value: float
    start_date: date
    end_date: date
    monthly_cap_per_user: float
    status: OfferStatusEnum

    model_config = {"from_attributes": True}

    @model_validator(mode="before")
    @classmethod
    def _from_orm(cls, data: Any) -> Any:
        """Map ORM model fields (percentage/fixed_amount/active) to API contract
        fields (cashback_type/cashback_value/status) when building from an ORM
        instance. Dicts that already carry the API-contract keys are passed through
        unchanged."""
        if hasattr(data, "percentage"):
            return {
                "id": data.id,
                "merchant_id": data.merchant_id,
                "cashback_type": (
                    CashbackTypeEnum.fixed
                    if data.fixed_amount is not None
                    else CashbackTypeEnum.percent
                ),
                "cashback_value": (
                    data.fixed_amount
                    if data.fixed_amount is not None
                    else data.percentage
                ),
                "start_date": data.start_date,
                "end_date": data.end_date,
                "monthly_cap_per_user": data.monthly_cap_per_user,
                "status": "active" if data.active else "inactive",
            }
        return data


class PaginatedOffersOut(BaseModel):
    data: list[OfferOut]
    pagination: PaginationOut


# --- GET /offers/active


class ActiveOfferOut(BaseModel):
    id: UUID
    merchant_name: str
    cashback_type: CashbackTypeEnum
    cashback_value: float
    monthly_cap: float
    start_date: date
    end_date: date


class PaginatedActiveOffersOut(BaseModel):
    data: list[ActiveOfferOut]
    pagination: PaginationOut


# --- GET /offers/{id}


class OfferDetailsOut(BaseModel):
    id: UUID
    merchant_name: str
    cashback_type: CashbackTypeEnum
    cashback_value: float
    monthly_cap: float
    start_date: date
    end_date: date
    status: OfferStatusEnum

    model_config = {"from_attributes": True}


# --- PATCH /offers/{id}/status


class OfferStatusUpdate(BaseModel):
    status: OfferStatusEnum


class OfferStatusOut(BaseModel):
    id: UUID
    status: OfferStatusEnum
