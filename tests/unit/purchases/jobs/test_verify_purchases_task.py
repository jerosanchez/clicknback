"""Unit tests for make_verify_purchases_task (composition root / task builder).

Verifies that the factory wires all collaborators correctly and returns a
zero-argument async callable that can be handed to the scheduler.

Module under test: app.purchases.jobs.verify_purchases._task
"""

from datetime import datetime, timezone
from typing import cast
from unittest.mock import AsyncMock, MagicMock, create_autospec

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.broker import MessageBrokerABC
from app.purchases.clients import CashbackClientABC, WalletsClientABC
from app.purchases.jobs.verify_purchases import (
    SimulatedPurchaseVerifier,
    make_verify_purchases_task,
)
from app.purchases.repositories import PurchaseRepositoryABC

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_REJECTION_MERCHANT_ID = "f0000000-0000-0000-0000-000000000001"
_MAX_ATTEMPTS = 3
_FIXED_NOW = datetime(2026, 3, 11, 12, 0, 0, tzinfo=timezone.utc)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_session_factory() -> tuple[async_sessionmaker[AsyncSession], AsyncMock]:
    session = AsyncMock()
    session.__aenter__ = AsyncMock(return_value=session)
    session.__aexit__ = AsyncMock(return_value=False)
    return (
        cast(async_sessionmaker[AsyncSession], MagicMock(return_value=session)),
        session,
    )


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def repository() -> MagicMock:
    return create_autospec(PurchaseRepositoryABC)


@pytest.fixture
def message_broker() -> MagicMock:
    return create_autospec(MessageBrokerABC)


@pytest.fixture
def wallets_client() -> MagicMock:
    return create_autospec(WalletsClientABC)


@pytest.fixture
def cashback_client() -> MagicMock:
    return create_autospec(CashbackClientABC)


# ---------------------------------------------------------------------------
# Factory smoke test
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_factory_returns_callable_and_runs_without_error_on_no_pending_purchases(
    repository: MagicMock,
    message_broker: MagicMock,
    wallets_client: MagicMock,
    cashback_client: MagicMock,
) -> None:
    """The factory returns a zero-arg async callable; invoking it with no pending purchases completes without error."""
    # Arrange
    session_factory, _ = _make_session_factory()
    repository.get_pending_purchases = AsyncMock(return_value=[])

    # Act
    task = make_verify_purchases_task(
        repository=repository,
        wallets_client=wallets_client,
        cashback_client=cashback_client,
        broker=message_broker,
        db_session_factory=session_factory,
        verifier=SimulatedPurchaseVerifier(
            rejection_merchant_id=_REJECTION_MERCHANT_ID
        ),
        max_attempts=_MAX_ATTEMPTS,
        retry_interval_seconds=0,
        datetime_provider=lambda: _FIXED_NOW,
    )

    # Assert
    assert callable(task)
    await task()
    repository.get_pending_purchases.assert_called_once()
