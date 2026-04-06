import os

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # --- database
    database_url: str

    # --- auth
    oauth_hash_key: str
    oauth_algorithm: str
    oauth_access_token_ttl: int = 15  # in minutes, default 15 minutes
    oauth_refresh_token_ttl: int = 43200  # in minutes; default 30 days (43200 min)

    # --- logging
    log_level: str = "INFO"

    # --- CORS
    # cors_allowed_origins: Comma-separated list from environment variable.
    # Pydantic automatically splits by comma: "https://app1.com,https://app2.com" → ["https://app1.com", "https://app2.com"]
    # Production: only explicit HTTPS origins (e.g., clicknback.com, partner origins).
    cors_allowed_origins: list[str] = ["https://clicknback.com"]
    # cors_allow_origin_regex: Optional regex pattern for local development only.
    # Example for dev: r"http://localhost(:\d+)?" to allow any localhost port.
    # This should remain None in production. Override in your local .env to enable.
    # See docs/design/api-cors-policy.md for complete CORS documentation.
    cors_allow_origin_regex: str | None = None

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
