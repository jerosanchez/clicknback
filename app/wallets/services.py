from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.wallets.repositories import WalletRepositoryABC
from app.wallets.schemas import WalletSummaryOut


class WalletService:
    def __init__(self, repository: WalletRepositoryABC) -> None:
        self.repository = repository

    async def get_wallet_summary(
        self, user_id: str, db: AsyncSession
    ) -> WalletSummaryOut:
        wallet = await self.repository.get_by_user_id(db, user_id)
        if wallet is None:
            return WalletSummaryOut(
                pending_balance=Decimal("0"),
                available_balance=Decimal("0"),
                paid_balance=Decimal("0"),
            )
        return WalletSummaryOut(
            pending_balance=wallet.pending_balance,
            available_balance=wallet.available_balance,
            paid_balance=wallet.paid_balance,
        )
