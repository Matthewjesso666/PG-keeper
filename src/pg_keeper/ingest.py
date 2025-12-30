from __future__ import annotations

import uuid
from pathlib import Path
from typing import Iterable, List

from rich.console import Console

from .config import Settings

console = Console()


def _get_chroma_client(settings: Settings):
    try:
        import chromadb
    except ImportError as exc:  # pragma: no cover - dependency check
        raise RuntimeError("chromadb is required for ingestion") from exc

    if settings.chroma_url:
        return chromadb.HttpClient(host=settings.chroma_url)
    return chromadb.Client()


def _read_text(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(path)

    if path.suffix.lower() in {".txt", ".md", ".log", ".json", ".yaml", ".yml"}:
        return path.read_text(encoding="utf-8", errors="ignore")

    # Fallback to binary-safe read for unknown extensions
    return path.read_text(encoding="utf-8", errors="ignore")


def _iter_files(paths: Iterable[Path]) -> Iterable[Path]:
    for item in paths:
        if item.is_dir():
            yield from (child for child in item.rglob("*") if child.is_file())
        elif item.is_file():
            yield item
        else:
            console.print(f"[yellow]Skipping missing path:[/] {item}")


def ingest_paths(paths: List[Path], settings: Settings, collection_name: str = "case-vault") -> int:
    client = _get_chroma_client(settings)
    collection = client.get_or_create_collection(collection_name)

    documents = []
    ids = []
    metadatas = []

    for file_path in _iter_files(paths):
        try:
            text = _read_text(file_path)
        except Exception as exc:  # pragma: no cover - defensive logging
            console.print(f"[red]Failed to read {file_path}: {exc}")
            continue

        doc_id = str(uuid.uuid4())
        ids.append(doc_id)
        documents.append(text)
        metadatas.append({
            "source": str(file_path),
            "name": file_path.name,
        })

    if not documents:
        console.print("[yellow]No documents ingested.")
        return 0

    collection.add(ids=ids, documents=documents, metadatas=metadatas)
    console.print(f"[green]Ingested[/] {len(documents)} documents into collection [bold]{collection_name}[/bold].")
    return len(documents)
