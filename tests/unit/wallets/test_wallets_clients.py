from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, Mock, create_autospec

import pytest

from app.cashback.models import CashbackTransaction
from app.cashback.repositories import CashbackTransactionRepositoryABC
from app.wallets.clients.cashback import CashbackClient, CashbackTransactionDTO

# ──────────────────────────────────────────────────────────────────────────────
# Fixtures
# ──────────────────────────────────────────────────────────────────────────────


@pytest.fixture
def cashback_repo_mock() -> Mock:
    return create_autospec(CashbackTransactionRepositoryABC)


@pytest.fixture
def cashback_client(cashback_repo_mock: Mock) -> CashbackClient:
    client = CashbackClient()
    client._repository = cashback_repo_mock  # pyright: ignore[reportPrivateUsage]
    return client


def _make_cashback_transaction(
    txn_id: str = "ct000001-0000-0000-0000-000000000001",
    purchase_id: str = "aa000001-0000-0000-0000-000000000001",
    amount: Decimal = Decimal("10.00"),
    status: str = "available",
) -> CashbackTransaction:
    txn = Mock(spec=CashbackTransaction)
    txn.id = txn_id
    txn.purchase_id = purchase_id
    txn.amount = amount
    txn.status = status
    txn.created_at = datetime(2026, 3, 28, 12, 0, 0, tzinfo=timezone.utc)
    return txn


# ──────────────────────────────────────────────────────────────────────────────
# CashbackClient.list_by_user_id
# ──────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_cashback_client_list_by_user_id_returns_mapped_dtos(
    cashback_client: CashbackClient,
    cashback_repo_mock: Mock,
) -> None:
    # Arrange
    db = AsyncMock()
    user_id = "b7e2c1a2-4f3a-4e2b-9c1a-8d2e3f4b5c6d"
    txn = _make_cashback_transaction()
    cashback_repo_mock.list_by_user_id.return_value = ([txn], 1)

    # Act
    dtos, total = await cashback_client.list_by_user_id(db, user_id, limit=10, offset=0)

    # Assert
    assert total == 1
    assert len(dtos) == 1
    dto = dtos[0]
    assert isinstance(dto, CashbackTransactionDTO)
    assert dto.id == txn.id
    assert dto.purchase_id == txn.purchase_id
    assert dto.amount == txn.amount
    assert dto.status == txn.status
    assert dto.created_at == txn.created_at


@pytest.mark.asyncio
async def test_cashback_client_list_by_user_id_returns_empty_list(
    cashback_client: CashbackClient,
    cashback_repo_mock: Mock,
) -> None:
    # Arrange
    db = AsyncMock()
    user_id = "b7e2c1a2-4f3a-4e2b-9c1a-8d2e3f4b5c6d"
    cashback_repo_mock.list_by_user_id.return_value = ([], 0)

    # Act
    dtos, total = await cashback_client.list_by_user_id(db, user_id, limit=10, offset=0)

    # Assert
    assert total == 0
    assert dtos == []


@pytest.mark.asyncio
async def test_cashback_client_list_by_user_id_delegates_pagination_params(
    cashback_client: CashbackClient,
    cashback_repo_mock: Mock,
) -> None:
    # Arrange
    db = AsyncMock()
    user_id = "b7e2c1a2-4f3a-4e2b-9c1a-8d2e3f4b5c6d"
    cashback_repo_mock.list_by_user_id.return_value = ([], 0)

    # Act
    await cashback_client.list_by_user_id(db, user_id, limit=20, offset=40)

    # Assert
    cashback_repo_mock.list_by_user_id.assert_called_once_with(db, user_id, 20, 40)
