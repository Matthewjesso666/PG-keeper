"""Local vault loader for PDFs and scanned documents."""
from __future__ import annotations

from pathlib import Path
from typing import Iterable, List


class VaultLoader:
    """Load documents stored in the local case vault."""

    def __init__(self, vault_path: str) -> None:
        self.vault_path = Path(vault_path)

    def discover_files(self, extensions: Iterable[str] = (".pdf", ".txt", ".md")) -> List[Path]:
        """Return a list of files in the vault with allowed extensions."""

        files: List[Path] = []
        for extension in extensions:
            files.extend(self.vault_path.rglob(f"*{extension}"))
        return files

    def load_bytes(self, path: Path) -> bytes:
        """Return the raw bytes of a document."""

        return path.read_bytes()
