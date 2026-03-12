import os

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # --- database
    database_url: str

    # --- auth
    oauth_hash_key: str
    oauth_algorithm: str
    oauth_token_ttl: int  # in minutes, for example, 15 minutes; no refresh tokens in this implementation

    # --- logging
    log_level: str = "INFO"

    # --- cashback policy
    max_cashback_percentage: float  # for example, 20%

    # pagination defaults
    default_page_size: int  # for example, 20 items per page
    max_page_size: int  # for example, 100 items per page

    # --- purchase confirmation background job
    purchase_confirmation_interval_seconds: int  # for example, 3600 seconds (1 hour)
    purchase_max_verification_attempts: int  # for example, 3 attempts
    # UUID of the merchant whose purchases are always rejected (rejection simulation).
    # Set to empty string to disable rejection simulation.
    rejection_merchant_id: str = ""

    model_config = {
        "env_file": ".env" if os.path.exists(".env") else None,
        "extra": "ignore",
    }


settings = Settings()  # type: ignore[call-arg]
