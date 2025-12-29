import datetime as dt
import hashlib
import json
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Set

import yaml

from services.drive_client import DriveClient
from services.gmail_client import GmailClient
from services.vault_loader import VaultLoader


@dataclass
class DocumentRecord:
    id: str
    source: str
    date: str
    entities: List[str]
    text: str
    hash: str = field(default="")
    metadata: Dict = field(default_factory=dict)


class Tagger:
    """Assigns tags using keyword rules with optional embedding-based similarity."""

    def __init__(self, config: Dict):
        tagger_cfg = config.get("ingestion", {}).get("tagger", {})
        self.keyword_entities: Dict[str, List[str]] = tagger_cfg.get("keyword_entities", {})
        self.embedding_model_name: Optional[str] = tagger_cfg.get("embedding_model")
        self._model = None
        self._label_embeddings: Dict[str, List[float]] = {}

    def _load_model(self):
        if self._model or not self.embedding_model_name:
            return
        try:
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(self.embedding_model_name)
        except Exception:
            self._model = None

    def tag(self, text: str) -> List[str]:
        entities: Set[str] = set()
        lowered = text.lower()
        for label, keywords in self.keyword_entities.items():
            if any(keyword.lower() in lowered for keyword in keywords):
                entities.add(label)

        self._load_model()
        if self._model and text.strip():
            try:
                doc_embedding = self._model.encode(text)
                entities.update(self._similarity_tags(doc_embedding))
            except Exception:
                pass
        return sorted(entities)

    def _similarity_tags(self, doc_embedding) -> Set[str]:
        try:
            import numpy as np
        except Exception:
            return set()

        tags: Set[str] = set()
        for label in self.keyword_entities:
            if label not in self._label_embeddings:
                self._label_embeddings[label] = self._model.encode(label)
            label_embedding = self._label_embeddings[label]
            score = float(
                np.dot(doc_embedding, label_embedding)
                / (np.linalg.norm(doc_embedding) * np.linalg.norm(label_embedding))
            )
            if score >= 0.4:
                tags.add(label)
        return tags


class IngestPipeline:
    """Pulls documents from Gmail, Drive, and the case vault, dedupes, and indexes them."""

    def __init__(self, config_path: str = "config/settings.yaml"):
        self.config_path = config_path
        self.config = self._load_config(config_path)
        self.index_dir = Path(self.config["ingestion"]["index_dir"])
        self.manifest_path = Path(self.config["ingestion"]["manifest_path"])
        self.index_dir.mkdir(parents=True, exist_ok=True)
        self.tagger = Tagger(self.config)
        self.gmail = GmailClient(self.config)
        self.drive = DriveClient(self.config)
        self.vault = VaultLoader(self.config)

    def _load_config(self, path: str) -> Dict:
        with open(path, "r") as f:
            return yaml.safe_load(f)

    def _load_manifest(self) -> Set[str]:
        hashes: Set[str] = set()
        if not self.manifest_path.exists():
            return hashes
        with open(self.manifest_path, "r") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    record = json.loads(line)
                    hashes.add(record["hash"])
                except json.JSONDecodeError:
                    continue
        return hashes

    def _append_manifest(self, record: DocumentRecord):
        with open(self.manifest_path, "a") as f:
            f.write(json.dumps({"id": record.id, "hash": record.hash, "source": record.source}) + "\n")

    def _hash_text(self, text: str) -> str:
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    def _normalize_date(self, value: Optional[str]) -> str:
        if not value:
            return dt.datetime.utcnow().isoformat()
        try:
            return dt.datetime.fromisoformat(value.replace("Z", "+00:00")).isoformat()
        except Exception:
            try:
                return dt.datetime.utcfromtimestamp(float(value)).isoformat()
            except Exception:
                return dt.datetime.utcnow().isoformat()

    def collect_documents(self) -> List[Dict]:
        docs: List[Dict] = []
        history_start = self.config["gmail"].get("history_start") or ""
        after = dt.datetime.fromisoformat(history_start) if history_start else None
        docs.extend(self.gmail.fetch_messages(after=after))
        docs.extend(self.drive.fetch_files())
        docs.extend(self.vault.iter_documents())
        return docs

    def _decode_drive_payload(self, doc: Dict) -> str:
        if doc.get("text"):
            return doc["text"]
        if "bytes" in doc and doc["bytes"]:
            try:
                return doc["bytes"].decode("utf-8")
            except Exception:
                return ""
        return ""

    def _record_from_doc(self, doc: Dict) -> DocumentRecord:
        text = doc.get("text") or self._decode_drive_payload(doc)
        record_id = doc.get("id") or uuid.uuid4().hex
        date_value = doc.get("date") or doc.get("modifiedTime")
        entities = self.tagger.tag(text)
        hash_value = self._hash_text(text)
        return DocumentRecord(
            id=record_id,
            source=doc.get("source", "unknown"),
            date=self._normalize_date(date_value),
            entities=entities,
            text=text,
            hash=hash_value,
            metadata={"name": doc.get("name"), "path": doc.get("path")},
        )

    def run_once(self) -> List[DocumentRecord]:
        existing_hashes = self._load_manifest()
        new_records: List[DocumentRecord] = []
        for doc in self.collect_documents():
            record = self._record_from_doc(doc)
            if record.hash in existing_hashes:
                continue
            self._write_record(record)
            self._append_manifest(record)
            existing_hashes.add(record.hash)
            new_records.append(record)
        return new_records

    def _write_record(self, record: DocumentRecord):
        record_path = self.index_dir / f"{record.id}.json"
        with open(record_path, "w") as f:
            json.dump(
                {
                    "id": record.id,
                    "source": record.source,
                    "date": record.date,
                    "entities": record.entities,
                    "text": record.text,
                    "hash": record.hash,
                    "metadata": record.metadata,
                },
                f,
                indent=2,
            )

    def run_forever(self):
        interval = int(self.config["ingestion"].get("schedule_minutes", 60))
        while True:
            self.run_once()
            time.sleep(interval * 60)


def main():
    pipeline = IngestPipeline()
    pipeline.run_once()


if __name__ == "__main__":
    main()
