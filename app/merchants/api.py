from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.current_user import get_current_admin_user
from app.core.database import get_db
from app.core.errors.builders import internal_server_error
from app.core.logging import logging
from app.merchants.composition import get_merchant_service
from app.merchants.schemas import MerchantCreate, MerchantOut
from app.merchants.services import MerchantService
from app.users.models import User

router = APIRouter(prefix="/api/v1")


@router.post("/merchants", status_code=status.HTTP_201_CREATED)
def create_merchant(
    create_data: MerchantCreate,
    merchant_service: MerchantService = Depends(get_merchant_service),
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_admin_user),
) -> MerchantOut:
    try:
        new_merchant = merchant_service.create_merchant(create_data.model_dump(), db)

    except Exception as e:
        logging.error(
            "An unexpected error occurred while creating a merchant.",
            extra={"error": str(e)},
        )
        raise internal_server_error()

    return new_merchant
