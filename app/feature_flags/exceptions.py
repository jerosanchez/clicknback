class FeatureFlagScopeIdRequiredException(Exception):
    def __init__(self, scope_type: str) -> None:
        super().__init__(f"scope_id is required when scope_type is '{scope_type}'.")
        self.scope_type = scope_type
