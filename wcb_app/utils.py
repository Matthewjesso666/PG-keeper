"""Shared utilities for WCB Super Advocate."""

import logging
import sys
from pathlib import Path
from typing import Optional

LOG_PATH = Path.cwd() / "logs" / "app.log"
DEFAULT_CASES_DIR = Path.cwd() / "cases"


def setup_logging() -> None:
    """Configure application logging."""
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    handlers = [
        logging.FileHandler(LOG_PATH, encoding="utf-8"),
        logging.StreamHandler(),
    ]
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=handlers,
    )


def get_resource_path(relative_path: str) -> Path:
    """Resolve resource paths for PyInstaller or source runs."""
    base_path: Path
    if getattr(sys, "frozen", False):
        base_path = Path(sys._MEIPASS)  # type: ignore[attr-defined]
    else:
        base_path = Path(__file__).resolve().parents[1]
    return base_path / relative_path


def ensure_dir(path: Path) -> Path:
    """Create a directory if missing."""
    path.mkdir(parents=True, exist_ok=True)
    return path


def safe_copy(src: Path, dest: Path) -> Path:
    """Copy a file while ensuring the destination directory exists."""
    ensure_dir(dest.parent)
    data = src.read_bytes()
    dest.write_bytes(data)
    return dest


def read_text_file(path: Path, fallback_message: Optional[str] = None) -> str:
    """Read a UTF-8 text file with a friendly fallback."""
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        if fallback_message:
            return fallback_message
        raise
