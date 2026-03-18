from app.wallets.repositories import WalletRepository
from app.wallets.services import WalletService


def get_wallet_repository() -> WalletRepository:
    return WalletRepository()


def get_wallet_service() -> WalletService:
    return WalletService(repository=get_wallet_repository())
