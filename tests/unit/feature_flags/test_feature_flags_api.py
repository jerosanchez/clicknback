from datetime import datetime, timezone
from typing import Any, AsyncGenerator, Generator
from unittest.mock import AsyncMock, Mock, create_autospec

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.core.current_user import get_current_admin_user
from app.core.database import get_async_db
from app.core.errors.builders import forbidden_error
from app.core.errors.codes import ErrorCode
from app.feature_flags.composition import get_feature_flag_service
from app.feature_flags.errors import ErrorCode as FeatureFlagErrorCode
from app.feature_flags.exceptions import FeatureFlagScopeIdRequiredException
from app.feature_flags.models import FeatureFlag
from app.feature_flags.services import FeatureFlagService
from app.main import app

# ──────────────────────────────────────────────────────────────────────────────
# Fixtures
# ──────────────────────────────────────────────────────────────────────────────


@pytest.fixture
def feature_flag_service_mock() -> Mock:
    return create_autospec(FeatureFlagService)


async def _mock_get_async_db() -> AsyncGenerator[AsyncMock, Any]:
    yield AsyncMock()


@pytest.fixture
def client(feature_flag_service_mock: Mock) -> Generator[TestClient, None, None]:
    app.dependency_overrides[get_async_db] = _mock_get_async_db
    app.dependency_overrides[get_feature_flag_service] = lambda: (
        feature_flag_service_mock
    )
    app.dependency_overrides[get_current_admin_user] = lambda: Mock()

    yield TestClient(app)

    app.dependency_overrides.clear()


@pytest.fixture
def non_admin_client(
    feature_flag_service_mock: Mock,
) -> Generator[TestClient, None, None]:
    def raise_forbidden() -> None:
        raise forbidden_error("Admin access required.", {})

    app.dependency_overrides[get_async_db] = _mock_get_async_db
    app.dependency_overrides[get_feature_flag_service] = lambda: (
        feature_flag_service_mock
    )
    app.dependency_overrides[get_current_admin_user] = raise_forbidden

    yield TestClient(app)

    app.dependency_overrides.clear()


def _make_flag(**kwargs: Any) -> FeatureFlag:
    """Build a minimal FeatureFlag ORM instance for tests."""
    defaults: dict[str, Any] = {
        "id": "7f3a1234-bc56-7890-def0-1234567890ab",
        "key": "purchase_confirmation_job",
        "enabled": True,
        "scope_type": "global",
        "scope_id": None,
        "description": None,
        "created_at": datetime(2026, 1, 15, 12, 0, 0, tzinfo=timezone.utc),
        "updated_at": datetime(2026, 1, 15, 14, 30, 0, tzinfo=timezone.utc),
    }
    defaults.update(kwargs)
    return FeatureFlag(**defaults)


def _assert_flag_out_response(data: dict[str, Any], flag: FeatureFlag) -> None:
    assert data["id"] == str(flag.id)
    assert data["key"] == flag.key
    assert data["enabled"] == flag.enabled
    assert data["scope_type"] == flag.scope_type
    assert data["scope_id"] == flag.scope_id
    assert data["description"] == flag.description


def _assert_error_payload(data: dict[str, Any], expected_code: str) -> None:
    assert "error" in data
    assert data["error"]["code"] == expected_code


# ──────────────────────────────────────────────────────────────────────────────
# PUT /api/v1/feature-flags/{key}
# ──────────────────────────────────────────────────────────────────────────────


def test_set_feature_flag_returns_200_on_success(
    client: TestClient,
    feature_flag_service_mock: Mock,
) -> None:
    # Arrange
    flag = _make_flag(enabled=False)
    feature_flag_service_mock.set_flag.return_value = flag

    # Act
    response = client.put(
        "/api/v1/feature-flags/purchase_confirmation_job",
        json={"enabled": False},
    )

    # Assert
    assert response.status_code == status.HTTP_200_OK
    _assert_flag_out_response(response.json(), flag)


def test_set_feature_flag_returns_200_with_all_fields(
    client: TestClient,
    feature_flag_service_mock: Mock,
) -> None:
    # Arrange
    merchant_id = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
    flag = _make_flag(
        scope_type="merchant",
        scope_id=merchant_id,
        enabled=True,
        description="Test flag",
    )
    feature_flag_service_mock.set_flag.return_value = flag

    # Act
    response = client.put(
        "/api/v1/feature-flags/fraud_check",
        json={
            "enabled": True,
            "scope_type": "merchant",
            "scope_id": merchant_id,
            "description": "Test flag",
        },
    )

    # Assert
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["scope_type"] == "merchant"
    assert data["scope_id"] == merchant_id
    assert data["description"] == "Test flag"
    assert data["created_at"] is not None
    assert data["updated_at"] is not None


def test_set_feature_flag_enforces_admin_user(
    non_admin_client: TestClient,
) -> None:
    # Act
    response = non_admin_client.put(
        "/api/v1/feature-flags/purchase_confirmation_job",
        json={"enabled": False},
    )

    # Assert
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_set_feature_flag_returns_422_on_invalid_key_format(
    client: TestClient,
    feature_flag_service_mock: Mock,
) -> None:
    # Arrange — key is not snake_case
    invalid_key = "PurchaseConfirmationJob"

    # Act
    response = client.put(
        f"/api/v1/feature-flags/{invalid_key}",
        json={"enabled": False},
    )

    # Assert
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    _assert_error_payload(response.json(), "VALIDATION_ERROR")


@pytest.mark.parametrize(
    "exception,expected_status,expected_code",
    [
        (
            FeatureFlagScopeIdRequiredException("merchant"),
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            FeatureFlagErrorCode.FEATURE_FLAG_SCOPE_ID_REQUIRED,
        ),
        (
            Exception("Unexpected failure"),
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            ErrorCode.INTERNAL_SERVER_ERROR,
        ),
    ],
)
def test_set_feature_flag_returns_error_on_exception(
    client: TestClient,
    feature_flag_service_mock: Mock,
    exception: Exception,
    expected_status: int,
    expected_code: str,
) -> None:
    # Arrange
    feature_flag_service_mock.set_flag.side_effect = exception

    # Act
    response = client.put(
        "/api/v1/feature-flags/purchase_confirmation_job",
        json={"enabled": False},
    )

    # Assert
    assert response.status_code == expected_status
    _assert_error_payload(response.json(), expected_code)


def test_set_feature_flag_returns_422_with_scope_type_in_details(
    client: TestClient,
    feature_flag_service_mock: Mock,
) -> None:
    # Arrange
    scope_type = "merchant"
    feature_flag_service_mock.set_flag.side_effect = (
        FeatureFlagScopeIdRequiredException(scope_type)
    )

    # Act
    response = client.put(
        "/api/v1/feature-flags/fraud_check",
        json={"enabled": False, "scope_type": scope_type},
    )

    # Assert
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    data = response.json()
    assert data["error"]["code"] == FeatureFlagErrorCode.FEATURE_FLAG_SCOPE_ID_REQUIRED
    assert data["error"]["details"]["scope_type"] == scope_type


# ──────────────────────────────────────────────────────────────────────────────
# GET /api/v1/feature-flags/{key}/evaluate
# ──────────────────────────────────────────────────────────────────────────────


def test_evaluate_feature_flag_returns_200_on_success(
    client: TestClient,
    feature_flag_service_mock: Mock,
) -> None:
    # Arrange
    feature_flag_service_mock.is_enabled.return_value = False

    # Act
    response = client.get("/api/v1/feature-flags/purchase_confirmation_job/evaluate")

    # Assert
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["key"] == "purchase_confirmation_job"
    assert data["enabled"] is False


@pytest.mark.parametrize(
    "exception,expected_status,expected_code",
    [
        (
            Exception("Unexpected failure"),
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            ErrorCode.INTERNAL_SERVER_ERROR,
        ),
    ],
)
def test_evaluate_feature_flag_returns_error_on_exception(
    client: TestClient,
    feature_flag_service_mock: Mock,
    exception: Exception,
    expected_status: int,
    expected_code: str,
) -> None:
    # Arrange
    feature_flag_service_mock.is_enabled.side_effect = exception

    # Act
    response = client.get("/api/v1/feature-flags/purchase_confirmation_job/evaluate")

    # Assert
    assert response.status_code == expected_status
    _assert_error_payload(response.json(), expected_code)


def test_evaluate_feature_flag_enforces_admin_user(
    non_admin_client: TestClient,
) -> None:
    # Act
    response = non_admin_client.get(
        "/api/v1/feature-flags/purchase_confirmation_job/evaluate"
    )

    # Assert
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_evaluate_feature_flag_returns_500_on_unexpected_error(
    client: TestClient,
    feature_flag_service_mock: Mock,
) -> None:
    # Arrange
    feature_flag_service_mock.is_enabled.side_effect = Exception("DB error")

    # Act
    response = client.get("/api/v1/feature-flags/purchase_confirmation_job/evaluate")

    # Assert
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    _assert_error_payload(response.json(), ErrorCode.INTERNAL_SERVER_ERROR)


# ──────────────────────────────────────────────────────────────────────────────
# GET /api/v1/feature-flags (list)
# ──────────────────────────────────────────────────────────────────────────────


def test_list_feature_flags_returns_200_with_all_flags(
    client: TestClient,
    feature_flag_service_mock: Mock,
) -> None:
    # Arrange
    flag1 = _make_flag(key="purchase_confirmation_job", enabled=True)
    flag2 = _make_flag(
        id="ff000001-0000-0000-0000-000000000002",
        key="purchase_confirmation_job",
        enabled=False,
        scope_type="merchant",
        scope_id="f0000000-0000-0000-0000-000000000001",
    )
    feature_flag_service_mock.list_flags.return_value = ([flag1, flag2], 2)

    # Act
    response = client.get("/api/v1/feature-flags")

    # Assert
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["total"] == 2
    assert len(data["items"]) == 2
    _assert_flag_out_response(data["items"][0], flag1)
    _assert_flag_out_response(data["items"][1], flag2)


@pytest.mark.parametrize(
    "exception,expected_status,expected_code",
    [
        (
            Exception("Unexpected failure"),
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            ErrorCode.INTERNAL_SERVER_ERROR,
        ),
    ],
)
def test_list_feature_flags_returns_error_on_exception(
    client: TestClient,
    feature_flag_service_mock: Mock,
    exception: Exception,
    expected_status: int,
    expected_code: str,
) -> None:
    # Arrange
    feature_flag_service_mock.list_flags.side_effect = exception

    # Act
    response = client.get("/api/v1/feature-flags")

    # Assert
    assert response.status_code == expected_status
    _assert_error_payload(response.json(), expected_code)


def test_list_feature_flags_enforces_admin_user(
    non_admin_client: TestClient,
) -> None:
    # Act
    response = non_admin_client.get("/api/v1/feature-flags")

    # Assert
    assert response.status_code == status.HTTP_403_FORBIDDEN
