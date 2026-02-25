"""Configuration management for the WCB agent."""
from __future__ import annotations

import os
from functools import lru_cache
from typing import Optional

from pydantic import BaseModel, Field, HttpUrl


class Settings(BaseModel):
    """Application settings loaded from environment variables."""

    openai_api_key: str = Field(...)
    google_client_id: str = Field(...)
    google_client_secret: str = Field(...)
    google_refresh_token: str = Field(...)
    case_vault_path: str = Field(...)

    webhook_base_url: Optional[HttpUrl] = Field(
        None,
        description="Optional public URL for receiving notifications or callbacks.",
    )


@lru_cache()
def get_settings() -> Settings:
    """Return cached settings from environment variables."""

    return Settings(
        openai_api_key=os.getenv("OPENAI_API_KEY", ""),
        google_client_id=os.getenv("GOOGLE_CLIENT_ID", ""),
        google_client_secret=os.getenv("GOOGLE_CLIENT_SECRET", ""),
        google_refresh_token=os.getenv("GOOGLE_REFRESH_TOKEN", ""),
        case_vault_path=os.getenv("CASE_VAULT_PATH", "./case-vault"),
        webhook_base_url=os.getenv("WEBHOOK_BASE_URL"),
    )
