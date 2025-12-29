"""Configuration management for the WCB agent."""
from functools import lru_cache
from typing import Optional

from pydantic import BaseSettings, Field, HttpUrl


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    openai_api_key: str = Field(..., env="OPENAI_API_KEY")
    google_client_id: str = Field(..., env="GOOGLE_CLIENT_ID")
    google_client_secret: str = Field(..., env="GOOGLE_CLIENT_SECRET")
    google_refresh_token: str = Field(..., env="GOOGLE_REFRESH_TOKEN")
    case_vault_path: str = Field(..., env="CASE_VAULT_PATH")

    webhook_base_url: Optional[HttpUrl] = Field(
        None,
        description="Optional public URL for receiving notifications or callbacks.",
    )

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Return cached settings to avoid redundant parsing."""

    return Settings()
