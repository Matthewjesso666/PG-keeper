"""Configuration loading for PG Keeper."""
from dataclasses import dataclass
import os
from pathlib import Path


@dataclass
class KeeperConfig:
    storage_root: Path
    gmail_query: str
    google_credentials_file: Path
    embedding_model: str
    openai_model: str
    openai_api_key: str | None


DEFAULT_STORAGE_ROOT = Path(os.environ.get("PG_KEEPER_STORAGE", "wcb-tools/documents")).expanduser()
DEFAULT_GMAIL_QUERY = os.environ.get(
    "PG_KEEPER_GMAIL_QUERY", "(subject:WCB OR \"Workers' Compensation Board\" OR WCB)"
)
DEFAULT_GOOGLE_CREDENTIALS_FILE = Path(
    os.environ.get("PG_KEEPER_GOOGLE_CREDENTIALS", "~/.config/pg_keeper/google_credentials.json")
).expanduser()
DEFAULT_EMBEDDING_MODEL = os.environ.get(
    "PG_KEEPER_EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"
)
DEFAULT_OPENAI_MODEL = os.environ.get("PG_KEEPER_OPENAI_MODEL", "gpt-4o-mini")
DEFAULT_OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")


def load_config() -> KeeperConfig:
    storage_root = DEFAULT_STORAGE_ROOT
    storage_root.mkdir(parents=True, exist_ok=True)

    return KeeperConfig(
        storage_root=storage_root,
        gmail_query=DEFAULT_GMAIL_QUERY,
        google_credentials_file=DEFAULT_GOOGLE_CREDENTIALS_FILE,
        embedding_model=DEFAULT_EMBEDDING_MODEL,
        openai_model=DEFAULT_OPENAI_MODEL,
        openai_api_key=DEFAULT_OPENAI_API_KEY,
    )
