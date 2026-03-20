from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.current_user import get_current_user
from app.core.database import get_async_db
from app.core.errors.builders import internal_server_error
from app.core.logging import logger
from app.users.models import User
from app.wallets.composition import get_wallet_service
from app.wallets.schemas import PaginatedWalletTransactionOut, WalletSummaryOut
from app.wallets.services import WalletService

router = APIRouter(prefix="/users", tags=["wallets"])


@router.get(
    "/me/wallet",
    status_code=status.HTTP_200_OK,
    description=(
        "Return the authenticated user's wallet summary "
        "(pending, available, and paid balances). "
        "All balances are zero for users with no cashback activity."
    ),
)
async def get_wallet_summary(
    service: WalletService = Depends(get_wallet_service),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
) -> WalletSummaryOut:
    try:
        return await service.get_wallet_summary(str(current_user.id), db)
    except Exception as e:
        logger.error(
            "An unexpected error occurred while retrieving wallet summary.",
            extra={"error": str(e)},
        )
        raise internal_server_error() from None


@router.get(
    "/me/wallet/transactions",
    status_code=status.HTTP_200_OK,
    description=(
        "Return a paginated list of the authenticated user's wallet transactions "
        "(cashback credits and reversals), ordered newest first."
    ),
)
async def list_wallet_transactions(
    limit: int = Query(
        10, ge=1, le=100, description="Number of items to return (1–100)."
    ),
    offset: int = Query(0, ge=0, description="Number of items to skip."),
    service: WalletService = Depends(get_wallet_service),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
) -> PaginatedWalletTransactionOut:
    try:
        return await service.list_wallet_transactions(
            str(current_user.id), limit, offset, db
        )
    except Exception as e:
        logger.error(
            "An unexpected error occurred while listing wallet transactions.",
            extra={"error": str(e)},
        )
        raise internal_server_error() from None
