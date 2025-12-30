import pathlib
from typing import Dict, Iterable, List

import pdfplumber
from pypdf import PdfReader


class VaultLoader:
    """Load local PDFs/scans from the case vault folder."""

    def __init__(self, config: Dict):
        self.vault_path = pathlib.Path(config["vault"]["path"]).expanduser().resolve()

    def iter_documents(self) -> Iterable[Dict]:
        if not self.vault_path.exists():
            return []

        documents: List[Dict] = []
        for pdf_path in sorted(self.vault_path.glob("**/*.pdf")):
            text = self._extract_text(pdf_path)
            documents.append(
                {
                    "id": pdf_path.stem,
                    "name": pdf_path.name,
                    "text": text,
                    "modifiedTime": pdf_path.stat().st_mtime,
                    "source": "vault",
                    "path": str(pdf_path),
                }
            )
        return documents

    def _extract_text(self, pdf_path: pathlib.Path) -> str:
        try:
            with pdfplumber.open(pdf_path) as pdf:
                return "\n".join(page.extract_text() or "" for page in pdf.pages)
        except Exception:
            reader = PdfReader(str(pdf_path))
            return "\n".join(page.extract_text() or "" for page in reader.pages)
