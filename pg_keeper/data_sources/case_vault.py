"""Local case vault ingestion."""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List

from pg_keeper.config import CaseVaultConfig
from pg_keeper.models import Category, Document, SourceType


@dataclass
class CaseVaultReader:
    config: CaseVaultConfig

    def iter_files(self) -> Iterable[Path]:
        for ext in self.config.allowed_extensions:
            yield from self.config.vault_path.rglob(f"*{ext}")

    def _hash_file(self, path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                digest.update(chunk)
        return digest.hexdigest()

    def _read_text(self, path: Path) -> str:
        if path.suffix.lower() in {".txt", ".md"}:
            return path.read_text(encoding="utf-8", errors="ignore")
        if path.suffix.lower() == ".pdf":
            import importlib.util

            if importlib.util.find_spec("PyPDF2") is None:
                raise ImportError("PyPDF2 is required to read PDF files")
            from PyPDF2 import PdfReader  # type: ignore

            reader = PdfReader(str(path))
            return "\n".join(page.extract_text() or "" for page in reader.pages)
        return ""

    def load_documents(self) -> List[Document]:
        documents: List[Document] = []
        for path in self.iter_files():
            content = self._read_text(path)
            documents.append(
                Document(
                    identifier=self._hash_file(path),
                    title=path.stem,
                    source=SourceType.CASE_VAULT,
                    content=content,
                    path=path,
                    category=Category.UNKNOWN,
                )
            )
        return documents
