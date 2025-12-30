from __future__ import annotations

from typing import List, Optional

from rich.console import Console

from .config import Settings

console = Console()


def _get_collection(settings: Settings, collection_name: str = "case-vault"):
    try:
        import chromadb
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("chromadb is required for chat") from exc

    client = chromadb.HttpClient(host=settings.chroma_url) if settings.chroma_url else chromadb.Client()
    return client.get_or_create_collection(collection_name)


def chat(query: str, settings: Settings, collection_name: str = "case-vault", top_k: int = 4) -> dict:
    collection = _get_collection(settings, collection_name)
    results = collection.query(query_texts=[query], n_results=top_k)
    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]

    context_snippets: List[str] = []
    for metadata, document in zip(metadatas, documents):
        source = metadata.get("source") if isinstance(metadata, dict) else None
        preview = document[:280] + ("..." if len(document) > 280 else "") if isinstance(document, str) else ""
        context_snippets.append(f"Source: {source}\n{preview}\n")

    response = {
        "query": query,
        "context": context_snippets,
        "answer": _draft_response(query, context_snippets, settings.model_name),
    }
    console.print("[green]Generated response with contextual snippets.")
    return response


def _draft_response(query: str, context_snippets: List[str], model_name: Optional[str]) -> str:
    context_preview = "\n\n".join(context_snippets) if context_snippets else "No context available."
    return (
        f"Model: {model_name or 'n/a'}\n"
        f"User query: {query}\n\n"
        f"Context:\n{context_preview}\n\n"
        "Summary: Provide a concise, factual reply that references the context above. "
        "If context is sparse, ask clarifying questions about the Workers' Compensation Board case."
    )
