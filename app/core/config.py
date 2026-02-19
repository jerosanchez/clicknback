import os

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # --- database
    database_url: str

    # --- auth
    oauth_hash_key: str
    oauth_algorithm: str
    oauth_token_ttl: int

    model_config = {
        "env_file": ".env" if os.path.exists(".env") else None,
        "extra": "ignore",
    }


settings = Settings()  # type: ignore[call-arg]
