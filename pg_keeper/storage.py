"""Local storage helpers for PG Keeper."""
from __future__ import annotations

import json
import shutil
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable


@dataclass
class DocumentRecord:
    source: str
    subject: str | None
    category: str
    received_at: datetime
    original_path: Path
    text_path: Path | None
    embeddings_path: Path | None
    module_outputs_path: Path | None


def safe_filename(name: str) -> str:
    return "".join(c if c.isalnum() or c in {"-", "_", "."} else "_" for c in name)


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def write_json(path: Path, payload: dict) -> None:
    ensure_dir(path.parent)
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, default=str)


def save_attachment(content_path: Path, storage_root: Path, category: str, label: str) -> Path:
    timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    category_dir = ensure_dir(storage_root / category)
    target_name = f"{timestamp}_{safe_filename(label)}{content_path.suffix}"
    target_path = category_dir / target_name
    shutil.copy2(content_path, target_path)
    return target_path


def save_text(text: str, storage_root: Path, category: str, label: str) -> Path:
    timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    category_dir = ensure_dir(storage_root / category)
    target_name = f"{timestamp}_{safe_filename(label)}.txt"
    target_path = category_dir / target_name
    ensure_dir(target_path.parent)
    with target_path.open("w", encoding="utf-8") as f:
        f.write(text)
    return target_path


def persist_document_record(record: DocumentRecord, storage_root: Path) -> Path:
    timeline_dir = ensure_dir(storage_root / "case_memory")
    target_path = timeline_dir / f"{record.received_at.strftime('%Y%m%dT%H%M%SZ')}_{safe_filename(record.subject or record.source)}.json"
    write_json(target_path, asdict(record))
    return target_path


def list_records(storage_root: Path) -> Iterable[Path]:
    memory_dir = storage_root / "case_memory"
    if not memory_dir.exists():
        return []
    return sorted(memory_dir.glob("*.json"))
