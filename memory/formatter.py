"""Formatting helpers for citation-ready retrieval outputs."""

from __future__ import annotations

from typing import Iterable, List

from .retriever import RetrievedChunk


class CitationFormatter:
    """Prepare retrieved chunks for display or downstream routing."""

    def format_citations(self, retrieved: Iterable[RetrievedChunk]) -> str:
        lines: List[str] = []
        for index, item in enumerate(retrieved, start=1):
            source = item.chunk.metadata.get("source", "unknown")
            pointer = item.chunk.metadata.get("pointer") or item.chunk.metadata.get("location")
            location = f" ({pointer})" if pointer else ""
            lines.append(f"[{index}] {source}{location}: {item.chunk.text}")
        return "\n".join(lines)

