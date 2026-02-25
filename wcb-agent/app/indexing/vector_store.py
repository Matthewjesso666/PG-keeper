"""Vector-like store utilities for organizing case documents."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Sequence

from langchain_core.documents import Document


@dataclass
class InMemoryCaseIndex:
    """Simple lexical index to avoid heavy external vector dependencies."""

    documents: List[Document]

    def similarity_search(self, query: str, k: int = 5) -> List[Document]:
        """Return top-k documents ranked by token overlap with query text."""

        query_terms = set(query.lower().split())
        ranked = sorted(
            self.documents,
            key=lambda doc: len(query_terms.intersection(set(doc.page_content.lower().split()))),
            reverse=True,
        )
        return ranked[:k]


def build_index(documents: Sequence[Document]) -> InMemoryCaseIndex:
    """Create a searchable in-memory index from case documents."""

    return InMemoryCaseIndex(documents=list(documents))


def similarity_search(store: InMemoryCaseIndex, query: str, k: int = 5) -> List[Document]:
    """Run a similarity search over the case index."""

    return store.similarity_search(query, k=k)
