from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.schemas import PaginationOut
from app.wallets.clients.cashback import CashbackClientABC
from app.wallets.repositories import WalletRepositoryABC
from app.wallets.schemas import (
    PaginatedWalletTransactionOut,
    WalletSummaryOut,
    WalletTransactionOut,
    WalletTransactionType,
)


class WalletService:
    def __init__(
        self,
        repository: WalletRepositoryABC,
        cashback_client: CashbackClientABC,
    ) -> None:
        self.repository = repository
        self.cashback_client = cashback_client

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

    async def list_wallet_transactions(
        self, user_id: str, limit: int, offset: int, db: AsyncSession
    ) -> PaginatedWalletTransactionOut:
        txns, total = await self.cashback_client.list_by_user_id(
            db, user_id, limit, offset
        )
        transactions = [
            WalletTransactionOut(
                id=txn.id,
                type=WalletTransactionType.CASHBACK_CREDIT,
                amount=txn.amount,
                status=txn.status,
                related_purchase_id=txn.purchase_id,
            )
            for txn in txns
        ]
        return PaginatedWalletTransactionOut(
            data=transactions,
            pagination=PaginationOut(offset=offset, limit=limit, total=total),
        )
