import os

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # --- database
    database_url: str

    # --- auth
    oauth_hash_key: str
    oauth_algorithm: str
    oauth_token_ttl: int

    # --- logging
    log_level: str = "INFO"

    # --- cashback policy
    max_cashback_percentage: float = 20.0

    # pagination defaults
    default_page_size: int = 20
    max_page_size: int = 100

    # --- purchase confirmation background job
    purchase_confirmation_interval_seconds: int = 60
    purchase_max_verification_attempts: int = 3
    # UUID of the merchant whose purchases are always rejected (rejection simulation).
    # Set to empty string to disable rejection simulation.
    rejection_merchant_id: str = ""

    model_config = {
        "env_file": ".env" if os.path.exists(".env") else None,
        "extra": "ignore",
    }


settings = Settings()  # type: ignore[call-arg]
