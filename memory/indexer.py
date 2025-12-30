"""Vector index construction for the normalized corpus.

This module avoids heavyweight dependencies by providing a lightweight TF-IDF
implementation. It can be replaced with libraries such as FAISS or ChromaDB if
available, but keeps a minimal footprint for testability.
"""

from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass
from typing import Dict, Iterable, List, Sequence


TOKEN_PATTERN = re.compile(r"\b\w+\b")


def _tokenize(text: str) -> List[str]:
    return TOKEN_PATTERN.findall(text.lower())


@dataclass
class DocumentChunk:
    """A single document chunk with accompanying metadata."""

    chunk_id: str
    text: str
    metadata: Dict[str, str]
    embedding: List[float]


class VectorIndex:
    """An in-memory vector index supporting cosine similarity search."""

    def __init__(
        self,
        *,
        vocabulary: Sequence[str],
        idf: Dict[str, float],
        document_vectors: List[List[float]],
        chunks: List[DocumentChunk],
    ) -> None:
        self.vocabulary = list(vocabulary)
        self.idf = idf
        self._vectors = document_vectors
        self._chunks = chunks

    def _normalize(self, vector: List[float]) -> List[float]:
        norm = math.sqrt(sum(value * value for value in vector))
        if norm == 0:
            return vector
        return [value / norm for value in vector]

    def _vectorize(self, text: str) -> List[float]:
        tokens = Counter(_tokenize(text))
        vector = [tokens.get(term, 0) * self.idf.get(term, 0) for term in self.vocabulary]
        return self._normalize(vector)

    def search(self, query: str, top_k: int = 5) -> List["SearchResult"]:
        """Return the top_k most similar chunks for the query."""

        query_vector = self._vectorize(query)
        scores: List[SearchResult] = []
        for vector, chunk in zip(self._vectors, self._chunks):
            score = self._cosine_similarity(query_vector, vector)
            scores.append(SearchResult(score=score, chunk=chunk))

        scores.sort(key=lambda result: result.score, reverse=True)
        return scores[:top_k]

    def _cosine_similarity(self, vector_a: List[float], vector_b: List[float]) -> float:
        return sum(a * b for a, b in zip(vector_a, vector_b))


@dataclass
class SearchResult:
    score: float
    chunk: DocumentChunk


class VectorIndexer:
    """Builds a vector index from a normalized corpus."""

    def __init__(self) -> None:
        self.vocabulary: List[str] = []
        self.idf: Dict[str, float] = {}

    def build_index(self, corpus: Iterable[Dict[str, str]]) -> VectorIndex:
        """Create a VectorIndex from an iterable of normalized corpus entries.

        Each corpus entry should provide ``id`` (unique identifier), ``text``
        (chunk content), and optional ``metadata`` dictionary.
        """

        tokenized_docs: List[List[str]] = []
        chunks: List[DocumentChunk] = []

        for entry in corpus:
            text = entry.get("text", "")
            metadata = entry.get("metadata", {}) or {}
            chunk_id = entry.get("id") or metadata.get("id") or str(len(chunks))
            tokens = _tokenize(text)
            tokenized_docs.append(tokens)
            chunks.append(
                DocumentChunk(
                    chunk_id=chunk_id,
                    text=text,
                    metadata=metadata,
                    embedding=[],  # populated after vectorization
                )
            )

        self._build_vocabulary(tokenized_docs)
        self._compute_idf(tokenized_docs)

        vectors = [self._normalize(self._vectorize_doc(tokens)) for tokens in tokenized_docs]
        for chunk, vector in zip(chunks, vectors):
            chunk.embedding = vector

        return VectorIndex(
            vocabulary=self.vocabulary,
            idf=self.idf,
            document_vectors=vectors,
            chunks=chunks,
        )

    def _build_vocabulary(self, tokenized_docs: List[List[str]]) -> None:
        vocab = set()
        for tokens in tokenized_docs:
            vocab.update(tokens)
        self.vocabulary = sorted(vocab)

    def _compute_idf(self, tokenized_docs: List[List[str]]) -> None:
        doc_count = len(tokenized_docs)
        df: Dict[str, int] = Counter()
        for tokens in tokenized_docs:
            for token in set(tokens):
                df[token] += 1
        self.idf = {term: math.log((1 + doc_count) / (1 + df_val)) + 1 for term, df_val in df.items()}

    def _vectorize_doc(self, tokens: List[str]) -> List[float]:
        counts = Counter(tokens)
        return [counts.get(term, 0) * self.idf.get(term, 0) for term in self.vocabulary]

    def _normalize(self, vector: List[float]) -> List[float]:
        norm = math.sqrt(sum(value * value for value in vector))
        if norm == 0:
            return vector
        return [value / norm for value in vector]

