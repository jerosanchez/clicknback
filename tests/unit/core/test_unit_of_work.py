from unittest.mock import AsyncMock

import pytest

from app.core.unit_of_work import SQLAlchemyUnitOfWork

# ──────────────────────────────────────────────────────────────────────────────
# SQLAlchemyUnitOfWork
# ──────────────────────────────────────────────────────────────────────────────


def test_unit_of_work_session_returns_injected_session() -> None:
    # Arrange
    mock_session = AsyncMock()
    uow = SQLAlchemyUnitOfWork(mock_session)

    # Act & Assert
    assert uow.session is mock_session


@pytest.mark.asyncio
async def test_unit_of_work_commit_delegates_to_session() -> None:
    # Arrange
    mock_session = AsyncMock()
    uow = SQLAlchemyUnitOfWork(mock_session)

    # Act
    await uow.commit()

    # Assert
    mock_session.commit.assert_called_once()


@pytest.mark.asyncio
async def test_unit_of_work_rollback_delegates_to_session() -> None:
    # Arrange
    mock_session = AsyncMock()
    uow = SQLAlchemyUnitOfWork(mock_session)

    # Act
    await uow.rollback()

    # Assert
    mock_session.rollback.assert_called_once()
