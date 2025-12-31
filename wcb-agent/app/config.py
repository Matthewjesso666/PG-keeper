"""Configuration management for the WCB agent."""
from functools import lru_cache
from typing import List, Optional

from pydantic import BaseSettings, Field, HttpUrl, field_validator


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    openai_api_key: str = Field(..., env="OPENAI_API_KEY")
    google_client_id: str = Field(..., env="GOOGLE_CLIENT_ID")
    google_client_secret: str = Field(..., env="GOOGLE_CLIENT_SECRET")
    google_refresh_token: str = Field(..., env="GOOGLE_REFRESH_TOKEN")
    case_vault_path: str = Field(..., env="CASE_VAULT_PATH")
    drive_folder_ids: List[str] = Field(
        default_factory=lambda: ["root"],
        env="GOOGLE_DRIVE_FOLDER_IDS",
        description="Comma-separated list of Drive folder IDs to scan for WCB documents.",
    )

    webhook_base_url: Optional[HttpUrl] = Field(
        None,
        description="Optional public URL for receiving notifications or callbacks.",
    )

    class Config:
        env_file = ".env"
        case_sensitive = True

    @field_validator("drive_folder_ids", mode="before")
    @classmethod
    def _split_drive_ids(cls, value: str | List[str] | None) -> List[str]:
        if value is None:
            return ["root"]
        if isinstance(value, list):
            return value
        return [item.strip() for item in value.split(",") if item.strip()]


@lru_cache()
def get_settings() -> Settings:
    """Return cached settings to avoid redundant parsing."""

    return Settings()
