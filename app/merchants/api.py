from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.merchants.composition import get_merchant_service
from app.merchants.schemas import MerchantCreate, MerchantOut
from app.merchants.services import MerchantService

router = APIRouter(prefix="/api/v1")


@router.post("/merchants", status_code=status.HTTP_201_CREATED)
def create_merchant(
    create_data: MerchantCreate,
    merchant_service: MerchantService = Depends(get_merchant_service),
    db: Session = Depends(get_db),
) -> MerchantOut:
    try:
        new_merchant = merchant_service.create_merchant(create_data.model_dump(), db)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    return new_merchant
