from app.wallets.clients.cashback import CashbackClient
from app.wallets.repositories import WalletRepository
from app.wallets.services import WalletService


def get_wallet_repository() -> WalletRepository:
    return WalletRepository()


def get_cashback_client() -> CashbackClient:
    return CashbackClient()


def get_wallet_service() -> WalletService:
    return WalletService(
        repository=get_wallet_repository(),
        cashback_client=get_cashback_client(),
    )
