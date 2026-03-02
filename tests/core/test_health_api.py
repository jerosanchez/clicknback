from unittest.mock import MagicMock, patch

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


# ──────────────────────────────────────────────────────────────────────────────
# GET /health/live
# ──────────────────────────────────────────────────────────────────────────────


def test_liveness_returns_200_on_success(client: TestClient) -> None:
    # Act
    response = client.get("/health/live")

    # Assert
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"status": "alive"}


# ──────────────────────────────────────────────────────────────────────────────
# GET /health/ready
# ──────────────────────────────────────────────────────────────────────────────


def test_readiness_returns_200_on_db_reachable(client: TestClient) -> None:
    # Arrange
    mock_conn = MagicMock()
    mock_conn.__enter__ = MagicMock(return_value=mock_conn)
    mock_conn.__exit__ = MagicMock(return_value=False)

    # Act
    with patch("app.core.health.engine.connect", return_value=mock_conn):
        response = client.get("/health/ready")

    # Assert
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"status": "ready"}


def test_readiness_returns_503_on_db_error(client: TestClient) -> None:
    # Arrange
    db_error = Exception("DB unavailable")

    # Act
    with patch("app.core.health.engine.connect", side_effect=db_error):
        response = client.get("/health/ready")

    # Assert
    assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    assert response.json() == {"status": "unavailable"}
