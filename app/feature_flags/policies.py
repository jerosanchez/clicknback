from app.feature_flags.exceptions import FeatureFlagScopeIdRequiredException


def validate_scope_id_required(scope_type: str, scope_id: str | None) -> None:
    """Enforce that scope_id is provided for non-global scope types."""
    if scope_type != "global" and scope_id is None:
        raise FeatureFlagScopeIdRequiredException(scope_type)
