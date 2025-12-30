"""Retriever utilities for fetching top-K chunks from the vector index."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List

from .indexer import DocumentChunk, VectorIndex, VectorIndexer


@dataclass
class RetrievedChunk:
    chunk: DocumentChunk
    score: float


class Retriever:
    """Wraps a VectorIndex to retrieve context for user queries."""

    def __init__(self, index: VectorIndex) -> None:
        self.index = index

    @classmethod
    def from_corpus(cls, corpus):
        index = VectorIndexer().build_index(corpus)
        return cls(index)

    def retrieve(self, query: str, top_k: int = 5) -> List[RetrievedChunk]:
        results = self.index.search(query, top_k=top_k)
        return [RetrievedChunk(chunk=result.chunk, score=result.score) for result in results]

