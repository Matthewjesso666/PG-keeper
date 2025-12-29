"""End-to-end ingestion pipeline for WCB artifacts."""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

from .categorizer import categorize
from .config import KeeperConfig
from .embeddings import EmbeddingIndexer
from .storage import DocumentRecord, persist_document_record, save_attachment, save_text


MODULES = [
    "Loophole Finder",
    "Fairness Review Expert",
    "Appeal Strategist",
    "Dirty Tactics Defender",
]


class CaseMemory:
    def __init__(self, storage_root: Path):
        self.storage_root = storage_root

    @property
    def memory_dir(self) -> Path:
        return self.storage_root / "case_memory"

    def save_module_outputs(self, identifier: str, outputs: Dict[str, str]) -> Path:
        path = self.memory_dir / f"{identifier}_modules.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as f:
            json.dump(outputs, f, indent=2)
        return path


class ModuleRouter:
    def __init__(self, model_name: str, api_key: str | None):
        self.model_name = model_name
        self.api_key = api_key

    def run_module(self, module_name: str, text: str) -> str:
        # Placeholder: connect your preferred LLM here.
        prompt = (
            f"You are {module_name} focused on WCB claims. Analyse the text below and return"
            f" concise, actionable notes. Text:\n{text[:4000]}"
        )
        # For offline safety we simply echo the prompt summary.
        return f"[{module_name}] {prompt[:500]}..."

    def route(self, text: str) -> Dict[str, str]:
        return {module: self.run_module(module, text) for module in MODULES}


class IngestionPipeline:
    def __init__(self, config: KeeperConfig):
        self.config = config
        self.memory = CaseMemory(config.storage_root)
        self.indexer = EmbeddingIndexer(config.embedding_model)
        self.router = ModuleRouter(config.openai_model, config.openai_api_key)

    def _build_identifier(self, subject: str | None) -> str:
        base = subject or "wcb_item"
        timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
        return f"{timestamp}_{base}"

    def process_item(self, text: str, attachments: Iterable[Path], subject: str | None, source: str) -> DocumentRecord:
        category = categorize(text)
        identifier = self._build_identifier(subject)

        text_path = save_text(text, self.config.storage_root, category, identifier)
        saved_attachments: List[Path] = []
        for attachment in attachments:
            saved = save_attachment(attachment, self.config.storage_root, category, attachment.name)
            saved_attachments.append(saved)

        chunks = self.indexer.build_index(text)
        embeddings_path = self.config.storage_root / category / f"{identifier}_embeddings.json"
        self.indexer.save_index(chunks, embeddings_path)

        module_outputs = self.router.route(text)
        modules_path = self.memory.save_module_outputs(identifier, module_outputs)

        record = DocumentRecord(
            source=source,
            subject=subject,
            category=category,
            received_at=datetime.utcnow(),
            original_path=text_path,
            text_path=text_path,
            embeddings_path=embeddings_path,
            module_outputs_path=modules_path,
        )
        persist_document_record(record, self.config.storage_root)
        return record

    def semantic_search(self, query: str, category: str | None = None, top_k: int = 5) -> List[Tuple[str, float, str]]:
        results: List[Tuple[str, float, str]] = []
        category_dir = self.config.storage_root / (category or "")
        for path in category_dir.rglob("*_embeddings.json"):
            chunks = self.indexer.load_index(path)
            matches = self.indexer.search(chunks, query, top_k=top_k)
            for score, match in matches:
                results.append((path.name, score, match.text))
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]
