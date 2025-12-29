"""Text splitting and embeddings for semantic search."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import List, Sequence

from sentence_transformers import SentenceTransformer  # type: ignore


@dataclass
class Chunk:
    id: str
    text: str
    vector: list[float]


class EmbeddingIndexer:
    def __init__(self, model_name: str):
        self.model_name = model_name
        self.model = SentenceTransformer(model_name)

    @staticmethod
    def split_text(text: str, chunk_size: int = 512, overlap: int = 50) -> List[str]:
        words = text.split()
        chunks: List[str] = []
        start = 0
        while start < len(words):
            end = start + chunk_size
            chunk_words = words[start:end]
            chunks.append(" ".join(chunk_words))
            if end >= len(words):
                break
            start = max(0, end - overlap)
        return chunks

    def build_index(self, text: str) -> List[Chunk]:
        parts = self.split_text(text)
        embeddings = self.model.encode(parts).tolist()
        return [Chunk(id=f"chunk-{i}", text=chunk, vector=emb) for i, (chunk, emb) in enumerate(zip(parts, embeddings))]

    @staticmethod
    def save_index(chunks: Sequence[Chunk], path: Path) -> None:
        payload = [chunk.__dict__ for chunk in chunks]
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)

    @staticmethod
    def load_index(path: Path) -> List[Chunk]:
        if not path.exists():
            return []
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        return [Chunk(**item) for item in data]

    @staticmethod
    def cosine_similarity(vec_a: list[float], vec_b: list[float]) -> float:
        import math

        dot = sum(a * b for a, b in zip(vec_a, vec_b))
        norm_a = math.sqrt(sum(a * a for a in vec_a))
        norm_b = math.sqrt(sum(b * b for b in vec_b))
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)

    def search(self, index: Sequence[Chunk], query: str, top_k: int = 5) -> List[tuple[float, Chunk]]:
        query_vec = self.model.encode([query]).tolist()[0]
        scored = [
            (self.cosine_similarity(query_vec, chunk.vector), chunk) for chunk in index
        ]
        scored.sort(key=lambda x: x[0], reverse=True)
        return scored[:top_k]
