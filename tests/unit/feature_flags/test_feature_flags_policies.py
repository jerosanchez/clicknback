import pytest

from app.feature_flags.exceptions import FeatureFlagScopeIdRequiredException
from app.feature_flags.policies import validate_scope_id_required

# ──────────────────────────────────────────────────────────────────────────────
# validate_scope_id_required
# ──────────────────────────────────────────────────────────────────────────────


def test_validate_scope_id_required_passes_for_global_without_scope_id() -> None:
    # Arrange / Act / Assert — no exception expected
    validate_scope_id_required("global", None)


def test_validate_scope_id_required_passes_for_global_with_scope_id() -> None:
    # Arrange / Act / Assert — global scope ignores scope_id entirely
    validate_scope_id_required("global", "any-id")


def test_validate_scope_id_required_passes_for_merchant_with_scope_id() -> None:
    # Arrange
    scope_id = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"

    # Act / Assert — no exception expected
    validate_scope_id_required("merchant", scope_id)


def test_validate_scope_id_required_passes_for_user_with_scope_id() -> None:
    # Arrange
    scope_id = "b7e2c1a2-4f3a-4e2b-9c1a-8d2e3f4b5c6d"

    # Act / Assert — no exception expected
    validate_scope_id_required("user", scope_id)


def test_validate_scope_id_required_raises_for_merchant_without_scope_id() -> None:
    # Act & Assert
    with pytest.raises(FeatureFlagScopeIdRequiredException) as exc_info:
        validate_scope_id_required("merchant", None)

    assert exc_info.value.scope_type == "merchant"


def test_validate_scope_id_required_raises_for_user_without_scope_id() -> None:
    # Act & Assert
    with pytest.raises(FeatureFlagScopeIdRequiredException) as exc_info:
        validate_scope_id_required("user", None)

    assert exc_info.value.scope_type == "user"
