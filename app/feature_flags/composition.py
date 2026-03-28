from app.feature_flags.repositories import FeatureFlagRepository
from app.feature_flags.services import FeatureFlagService


def get_feature_flag_repository() -> FeatureFlagRepository:
    return FeatureFlagRepository()


def get_feature_flag_service() -> FeatureFlagService:
    return FeatureFlagService(repository=get_feature_flag_repository())
