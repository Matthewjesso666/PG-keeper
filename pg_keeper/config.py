"""Configuration helpers for PG-keeper."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional


@dataclass
class GoogleAuthConfig:
    """Paths to Google API credentials.

    The tokens are not loaded directly in this module so tests can run without
    the Google client libraries installed.
    """

    credentials_file: Path
    token_file: Optional[Path] = None
    scopes: List[str] = field(
        default_factory=lambda: [
            "https://www.googleapis.com/auth/gmail.readonly",
            "https://www.googleapis.com/auth/drive.readonly",
        ]
    )


@dataclass
class CaseVaultConfig:
    vault_path: Path
    allowed_extensions: List[str] = field(default_factory=lambda: [".pdf", ".txt", ".md"])


@dataclass
class AgentConfig:
    """Top-level configuration for the case agent."""

    google: Optional[GoogleAuthConfig] = None
    case_vault: Optional[CaseVaultConfig] = None
    llm_model: str = "openai/gpt-4.1-mini"
    response_recipient: str = "Claims Manager"
    dry_run: bool = True
