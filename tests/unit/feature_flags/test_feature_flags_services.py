from datetime import datetime, timezone
from typing import Any
from unittest.mock import AsyncMock, Mock, create_autospec

import pytest

from app.feature_flags.exceptions import FeatureFlagScopeIdRequiredException
from app.feature_flags.models import FeatureFlag
from app.feature_flags.repositories import FeatureFlagRepositoryABC
from app.feature_flags.schemas import FeatureFlagSet
from app.feature_flags.services import FeatureFlagService

# ──────────────────────────────────────────────────────────────────────────────
# Fixtures
# ──────────────────────────────────────────────────────────────────────────────


@pytest.fixture
def feature_flag_repository() -> Mock:
    return create_autospec(FeatureFlagRepositoryABC)


@pytest.fixture
def feature_flag_service(feature_flag_repository: Mock) -> FeatureFlagService:
    return FeatureFlagService(repository=feature_flag_repository)


def _make_uow() -> Mock:
    """Create a fresh mock UnitOfWork for write service tests."""
    uow = Mock()
    uow.session = AsyncMock()
    uow.commit = AsyncMock()
    uow.rollback = AsyncMock()
    return uow


def _make_flag(**kwargs: Any) -> FeatureFlag:
    """Build a minimal FeatureFlag ORM instance for tests."""
    defaults: dict[str, Any] = {
        "id": "ff000001-0000-0000-0000-000000000001",
        "key": "purchase_confirmation_job",
        "enabled": True,
        "scope_type": "global",
        "scope_id": None,
        "description": None,
        "created_at": datetime(2026, 1, 15, 12, 0, 0, tzinfo=timezone.utc),
        "updated_at": datetime(2026, 1, 15, 12, 0, 0, tzinfo=timezone.utc),
    }
    defaults.update(kwargs)
    return FeatureFlag(**defaults)


# ──────────────────────────────────────────────────────────────────────────────
# FeatureFlagService.set_flag — happy paths
# ──────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_set_flag_creates_new_global_flag_on_success(
    feature_flag_service: FeatureFlagService,
    feature_flag_repository: Mock,
) -> None:
    # Arrange
    uow = _make_uow()
    data = FeatureFlagSet(enabled=False)
    new_flag = _make_flag(enabled=False)
    feature_flag_repository.get_by_key_and_scope.return_value = None
    feature_flag_repository.upsert.return_value = new_flag

    # Act
    result = await feature_flag_service.set_flag("purchase_confirmation_job", data, uow)

    # Assert
    assert result == new_flag
    uow.commit.assert_called_once()


@pytest.mark.asyncio
async def test_set_flag_updates_existing_flag_on_success(
    feature_flag_service: FeatureFlagService,
    feature_flag_repository: Mock,
) -> None:
    # Arrange
    uow = _make_uow()
    existing_flag = _make_flag(enabled=True)
    data = FeatureFlagSet(enabled=False, description="Paused")
    updated_flag = _make_flag(enabled=False, description="Paused")
    feature_flag_repository.get_by_key_and_scope.return_value = existing_flag
    feature_flag_repository.upsert.return_value = updated_flag

    # Act
    result = await feature_flag_service.set_flag("purchase_confirmation_job", data, uow)

    # Assert
    assert result == updated_flag
    assert existing_flag.enabled is False
    uow.commit.assert_called_once()


@pytest.mark.asyncio
async def test_set_flag_passes_scope_id_to_repository(
    feature_flag_service: FeatureFlagService,
    feature_flag_repository: Mock,
) -> None:
    # Arrange
    uow = _make_uow()
    merchant_id = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
    data = FeatureFlagSet(
        enabled=False,
        scope_type="merchant",
        scope_id=merchant_id,  # type: ignore[arg-type]
    )
    new_flag = _make_flag(scope_type="merchant", scope_id=merchant_id, enabled=False)
    feature_flag_repository.get_by_key_and_scope.return_value = None
    feature_flag_repository.upsert.return_value = new_flag

    # Act
    result = await feature_flag_service.set_flag("fraud_check", data, uow)

    # Assert
    assert result == new_flag
    feature_flag_repository.get_by_key_and_scope.assert_called_once_with(
        uow.session, "fraud_check", "merchant", merchant_id
    )
    uow.commit.assert_called_once()


# ──────────────────────────────────────────────────────────────────────────────
# FeatureFlagService.set_flag — sad paths
# ──────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_set_flag_raises_scope_id_required_for_merchant_without_scope_id(
    feature_flag_service: FeatureFlagService,
    feature_flag_repository: Mock,
) -> None:
    # Arrange
    uow = _make_uow()
    data = FeatureFlagSet(enabled=False, scope_type="merchant")

    # Act & Assert
    with pytest.raises(FeatureFlagScopeIdRequiredException) as exc_info:
        await feature_flag_service.set_flag("fraud_check", data, uow)

    assert exc_info.value.scope_type == "merchant"
    uow.commit.assert_not_called()


@pytest.mark.asyncio
async def test_set_flag_raises_scope_id_required_for_user_without_scope_id(
    feature_flag_service: FeatureFlagService,
    feature_flag_repository: Mock,
) -> None:
    # Arrange
    uow = _make_uow()
    data = FeatureFlagSet(enabled=True, scope_type="user")

    # Act & Assert
    with pytest.raises(FeatureFlagScopeIdRequiredException) as exc_info:
        await feature_flag_service.set_flag("new_feature", data, uow)

    assert exc_info.value.scope_type == "user"
    uow.commit.assert_not_called()


# ──────────────────────────────────────────────────────────────────────────────
# FeatureFlagService.is_enabled — fail-open resolution
# ──────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_is_enabled_returns_true_when_no_flag_exists(
    feature_flag_service: FeatureFlagService,
    feature_flag_repository: Mock,
) -> None:
    # Arrange
    db = AsyncMock()
    feature_flag_repository.get_by_key_and_scope.return_value = None

    # Act
    result = await feature_flag_service.is_enabled("unknown_flag", db)

    # Assert
    assert result is True


@pytest.mark.asyncio
async def test_is_enabled_returns_global_flag_value_when_set(
    feature_flag_service: FeatureFlagService,
    feature_flag_repository: Mock,
) -> None:
    # Arrange
    db = AsyncMock()
    global_flag = _make_flag(enabled=False)
    feature_flag_repository.get_by_key_and_scope.return_value = global_flag

    # Act
    result = await feature_flag_service.is_enabled("purchase_confirmation_job", db)

    # Assert
    assert result is False


@pytest.mark.asyncio
async def test_is_enabled_returns_scoped_flag_over_global(
    feature_flag_service: FeatureFlagService,
    feature_flag_repository: Mock,
) -> None:
    # Arrange
    db = AsyncMock()
    merchant_id = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
    scoped_flag = _make_flag(scope_type="merchant", scope_id=merchant_id, enabled=False)
    # First call returns scoped; second call (global) should not be reached
    feature_flag_repository.get_by_key_and_scope.return_value = scoped_flag

    # Act
    result = await feature_flag_service.is_enabled(
        "purchase_confirmation_job",
        db,
        scope_type="merchant",
        scope_id=merchant_id,
    )

    # Assert
    assert result is False
    feature_flag_repository.get_by_key_and_scope.assert_called_once_with(
        db, "purchase_confirmation_job", "merchant", merchant_id
    )


@pytest.mark.asyncio
async def test_is_enabled_falls_back_to_global_when_scoped_flag_missing(
    feature_flag_service: FeatureFlagService,
    feature_flag_repository: Mock,
) -> None:
    # Arrange
    db = AsyncMock()
    merchant_id = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
    global_flag = _make_flag(enabled=True)
    # Scoped flag not found → fall through to global
    feature_flag_repository.get_by_key_and_scope.side_effect = [None, global_flag]

    # Act
    result = await feature_flag_service.is_enabled(
        "purchase_confirmation_job",
        db,
        scope_type="merchant",
        scope_id=merchant_id,
    )

    # Assert
    assert result is True


# ──────────────────────────────────────────────────────────────────────────────
# FeatureFlagService.list_flags
# ──────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_list_flags_returns_all_flags_without_filters(
    feature_flag_service: FeatureFlagService,
    feature_flag_repository: Mock,
) -> None:
    # Arrange
    db = AsyncMock()
    flag1 = _make_flag(key="purchase_confirmation_job", enabled=True)
    flag2 = _make_flag(
        id="ff000001-0000-0000-0000-000000000002",
        key="purchase_confirmation_job",
        enabled=False,
        scope_type="merchant",
    )
    feature_flag_repository.list.return_value = ([flag1, flag2], 2)

    # Act
    flags, total = await feature_flag_service.list_flags(db)

    # Assert
    assert len(flags) == 2
    assert total == 2
    assert flags[0] == flag1
    assert flags[1] == flag2
    feature_flag_repository.list.assert_called_once_with(db, None, None, None)


@pytest.mark.asyncio
async def test_list_flags_filters_by_key(
    feature_flag_service: FeatureFlagService,
    feature_flag_repository: Mock,
) -> None:
    # Arrange
    db = AsyncMock()
    flag = _make_flag(key="purchase_confirmation_job")
    feature_flag_repository.list.return_value = ([flag], 1)

    # Act
    flags, total = await feature_flag_service.list_flags(
        db, key="purchase_confirmation_job"
    )

    # Assert
    assert len(flags) == 1
    assert total == 1
    feature_flag_repository.list.assert_called_once_with(
        db, "purchase_confirmation_job", None, None
    )


@pytest.mark.asyncio
async def test_list_flags_filters_by_scope_type(
    feature_flag_service: FeatureFlagService,
    feature_flag_repository: Mock,
) -> None:
    # Arrange
    db = AsyncMock()
    flag = _make_flag(scope_type="merchant")
    feature_flag_repository.list.return_value = ([flag], 1)

    # Act
    flags, total = await feature_flag_service.list_flags(db, scope_type="merchant")

    # Assert
    assert len(flags) == 1
    assert total == 1
    feature_flag_repository.list.assert_called_once_with(db, None, "merchant", None)


@pytest.mark.asyncio
async def test_list_flags_filters_by_scope_id(
    feature_flag_service: FeatureFlagService,
    feature_flag_repository: Mock,
) -> None:
    # Arrange
    db = AsyncMock()
    scope_id = "f0000000-0000-0000-0000-000000000001"
    flag = _make_flag(scope_id=scope_id)
    feature_flag_repository.list.return_value = ([flag], 1)

    # Act
    flags, total = await feature_flag_service.list_flags(db, scope_id=scope_id)

    # Assert
    assert len(flags) == 1
    assert total == 1
    feature_flag_repository.list.assert_called_once_with(db, None, None, scope_id)


@pytest.mark.asyncio
async def test_list_flags_returns_empty_when_no_match(
    feature_flag_service: FeatureFlagService,
    feature_flag_repository: Mock,
) -> None:
    # Arrange
    db = AsyncMock()
    feature_flag_repository.list.return_value = ([], 0)

    # Act
    flags, total = await feature_flag_service.list_flags(db, key="nonexistent")

    # Assert
    assert len(flags) == 0
    assert total == 0


# ──────────────────────────────────────────────────────────────────────────────
# FeatureFlagService.evaluate_scopes — batch scope evaluation
# ──────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_evaluate_scopes_returns_empty_dict_for_empty_scopes(
    feature_flag_service: FeatureFlagService,
    feature_flag_repository: Mock,
) -> None:
    # Arrange
    db = AsyncMock()

    # Act
    result = await feature_flag_service.evaluate_scopes("auto_confirm", db, [])

    # Assert
    assert result == {}
    # Should not call repository if no scopes provided
    feature_flag_repository.get_multiple_by_key_and_scopes.assert_not_called()


@pytest.mark.asyncio
async def test_evaluate_scopes_all_scopes_enabled_with_scoped_flags(
    feature_flag_service: FeatureFlagService,
    feature_flag_repository: Mock,
) -> None:
    # Arrange
    db = AsyncMock()
    user_id = "user-123"
    merchant_id = "merchant-456"
    scopes = [("user", user_id), ("merchant", merchant_id)]

    scoped_flags = [
        _make_flag(scope_type="user", scope_id=user_id, enabled=True),
        _make_flag(scope_type="merchant", scope_id=merchant_id, enabled=True),
    ]
    feature_flag_repository.get_multiple_by_key_and_scopes.return_value = scoped_flags

    # Act
    result = await feature_flag_service.evaluate_scopes("auto_confirm", db, scopes)

    # Assert
    assert result == {
        ("user", user_id): True,
        ("merchant", merchant_id): True,
    }


@pytest.mark.asyncio
async def test_evaluate_scopes_fail_open_when_no_flags_exist(
    feature_flag_service: FeatureFlagService,
    feature_flag_repository: Mock,
) -> None:
    # Arrange
    db = AsyncMock()
    user_id = "user-123"
    merchant_id = "merchant-456"
    scopes = [("user", user_id), ("merchant", merchant_id)]

    # No flags found → should fail-open to True
    feature_flag_repository.get_multiple_by_key_and_scopes.return_value = []

    # Act
    result = await feature_flag_service.evaluate_scopes("auto_confirm", db, scopes)

    # Assert
    assert result == {
        ("user", user_id): True,
        ("merchant", merchant_id): True,
    }


@pytest.mark.asyncio
async def test_evaluate_scopes_scoped_flag_disabled_overrides_global_enabled(
    feature_flag_service: FeatureFlagService,
    feature_flag_repository: Mock,
) -> None:
    # Arrange
    db = AsyncMock()
    user_id = "user-123"
    merchant_id = "merchant-456"
    scopes = [("user", user_id), ("merchant", merchant_id)]

    flags = [
        _make_flag(scope_type="global", scope_id=None, enabled=True),
        _make_flag(scope_type="user", scope_id=user_id, enabled=False),  # Disabled
    ]
    feature_flag_repository.get_multiple_by_key_and_scopes.return_value = flags

    # Act
    result = await feature_flag_service.evaluate_scopes("auto_confirm", db, scopes)

    # Assert
    # user scope disabled (scoped flag wins)
    # merchant scope falls back to global enabled
    assert result == {
        ("user", user_id): False,
        ("merchant", merchant_id): True,
    }


@pytest.mark.asyncio
async def test_evaluate_scopes_global_flag_disabled_affects_all_without_scoped_override(
    feature_flag_service: FeatureFlagService,
    feature_flag_repository: Mock,
) -> None:
    # Arrange
    db = AsyncMock()
    user_id = "user-123"
    merchant_id = "merchant-456"
    scopes = [("user", user_id), ("merchant", merchant_id)]

    flags = [
        _make_flag(
            scope_type="global", scope_id=None, enabled=False
        ),  # Global disabled
        _make_flag(scope_type="user", scope_id=user_id, enabled=True),  # Scoped enabled
    ]
    feature_flag_repository.get_multiple_by_key_and_scopes.return_value = flags

    # Act
    result = await feature_flag_service.evaluate_scopes("auto_confirm", db, scopes)

    # Assert
    # user scope enabled (scoped flag takes precedence)
    # merchant scope disabled (global flag is disabled, no scoped override)
    assert result == {
        ("user", user_id): True,
        ("merchant", merchant_id): False,
    }


@pytest.mark.asyncio
async def test_evaluate_scopes_scoped_enabled_overrides_global_disabled(
    feature_flag_service: FeatureFlagService,
    feature_flag_repository: Mock,
) -> None:
    # Arrange
    db = AsyncMock()
    user_id = "user-123"
    merchant_id = "merchant-456"
    scopes = [("user", user_id), ("merchant", merchant_id)]

    flags = [
        _make_flag(
            scope_type="global", scope_id=None, enabled=False
        ),  # Global disabled
        _make_flag(
            scope_type="user", scope_id=user_id, enabled=True
        ),  # Scoped enabled - overrides global
    ]
    feature_flag_repository.get_multiple_by_key_and_scopes.return_value = flags

    # Act
    result = await feature_flag_service.evaluate_scopes("auto_confirm", db, scopes)

    # Assert
    # user scope enabled (scoped flag overrides disabled global)
    # merchant scope disabled (global flag value)
    assert result == {
        ("user", user_id): True,
        ("merchant", merchant_id): False,
    }


@pytest.mark.asyncio
async def test_evaluate_scopes_mixed_state_multiple_scopes(
    feature_flag_service: FeatureFlagService,
    feature_flag_repository: Mock,
) -> None:
    # Arrange
    db = AsyncMock()
    scopes = [
        ("user", "user-123"),
        ("merchant", "merchant-456"),
        ("wallet", "wallet-789"),
    ]

    flags = [
        _make_flag(scope_type="global", scope_id=None, enabled=False),
        # user scope: enabled (overrides global disabled)
        _make_flag(scope_type="user", scope_id="user-123", enabled=True),
        # merchant scope: disabled (overrides global disabled, explicit disable)
        _make_flag(scope_type="merchant", scope_id="merchant-456", enabled=False),
        # wallet scope: no flag → falls back to global (disabled)
    ]
    feature_flag_repository.get_multiple_by_key_and_scopes.return_value = flags

    # Act
    result = await feature_flag_service.evaluate_scopes("auto_confirm", db, scopes)

    # Assert
    assert result == {
        ("user", "user-123"): True,
        ("merchant", "merchant-456"): False,
        ("wallet", "wallet-789"): False,  # Falls back to global (disabled)
    }


@pytest.mark.asyncio
async def test_evaluate_scopes_only_global_flag_present(
    feature_flag_service: FeatureFlagService,
    feature_flag_repository: Mock,
) -> None:
    # Arrange
    db = AsyncMock()
    scopes = [("user", "user-123"), ("merchant", "merchant-456")]

    # Only global flag exists
    flags = [_make_flag(scope_type="global", scope_id=None, enabled=True)]
    feature_flag_repository.get_multiple_by_key_and_scopes.return_value = flags

    # Act
    result = await feature_flag_service.evaluate_scopes("auto_confirm", db, scopes)

    # Assert
    # All scopes use global flag value
    assert result == {
        ("user", "user-123"): True,
        ("merchant", "merchant-456"): True,
    }
