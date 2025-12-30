from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class Settings:
    data_dir: Path
    chroma_url: Optional[str] = None
    api_key: Optional[str] = None
    model_name: str = "gpt-4o-mini"

    @classmethod
    def from_env(cls) -> "Settings":
        data_dir = Path(os.getenv("PG_KEEPER_DATA_DIR", "./data")).expanduser()
        chroma_url = os.getenv("PG_KEEPER_CHROMA_URL")
        api_key = os.getenv("PG_KEEPER_API_KEY")
        model_name = os.getenv("PG_KEEPER_MODEL", "gpt-4o-mini")
        data_dir.mkdir(parents=True, exist_ok=True)
        return cls(data_dir=data_dir, chroma_url=chroma_url, api_key=api_key, model_name=model_name)
