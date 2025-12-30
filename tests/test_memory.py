import json
from pathlib import Path

import pytest

from memory.formatter import CitationFormatter
from memory.indexer import VectorIndexer
from memory.retriever import Retriever


@pytest.fixture
def small_corpus():
    return [
        {"id": "a", "text": "Workers compensation policy overview", "metadata": {"source": "policy", "pointer": "p1"}},
        {"id": "b", "text": "Appeal strategy and deadlines", "metadata": {"source": "guide", "pointer": "p2"}},
        {"id": "c", "text": "Email correspondence about claim status", "metadata": {"source": "email", "pointer": "p3"}},
    ]


def test_retrieval_prefers_relevant_chunks(small_corpus):
    retriever = Retriever(VectorIndexer().build_index(small_corpus))

    results = retriever.retrieve("appeal deadlines", top_k=2)
    assert results, "Should return at least one result"
    assert results[0].chunk.chunk_id == "b"
    assert results[0].chunk.text.startswith("Appeal strategy")


def test_citation_formatting(small_corpus, tmp_path: Path):
    retriever = Retriever(VectorIndexer().build_index(small_corpus))
    results = retriever.retrieve("claim status", top_k=2)
    formatter = CitationFormatter()

    formatted = formatter.format_citations(results)
    lines = formatted.split("\n")
    assert lines[0].startswith("[1] email"), "First line should reference email source"
    assert "p3" in lines[0]

    # Verify JSONL logging structure aligns with retrieval payload expectations
    log_path = tmp_path / "session.jsonl"
    from cli.chat import _log_interaction  # local import to avoid circular refs

    _log_interaction(log_path, "question", results, "answer")
    logged = log_path.read_text(encoding="utf-8").strip().split("\n")
    payload = json.loads(logged[0])
    assert payload["user_input"] == "question"
    assert payload["context"][0]["chunk_id"] == results[0].chunk.chunk_id
    assert payload["response"] == "answer"

