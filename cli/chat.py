"""Interactive chat loop that retrieves context and routes responses."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
from pathlib import Path
from typing import Callable, Iterable, List

from memory.formatter import CitationFormatter
from memory.retriever import RetrievedChunk, Retriever


def _resolve_router(router: object) -> Callable[[str, List[RetrievedChunk]], str]:
    if callable(router):
        return router  # type: ignore[return-value]
    if hasattr(router, "respond") and callable(getattr(router, "respond")):
        return lambda message, context: router.respond(message, context)  # type: ignore[arg-type]
    raise ValueError("Router must be callable or expose a 'respond' method")


def run_chat_loop(
    *,
    retriever: Retriever,
    router: object,
    formatter: CitationFormatter | None = None,
    log_dir: str | os.PathLike[str] = "logs/sessions",
) -> None:
    formatter = formatter or CitationFormatter()
    dispatch = _resolve_router(router)
    Path(log_dir).mkdir(parents=True, exist_ok=True)
    log_path = Path(log_dir) / f"session-{dt.datetime.utcnow().isoformat()}Z.jsonl"

    print("Type 'exit' or 'quit' to leave the chat.")
    while True:
        try:
            user_input = input("You: ").strip()
        except EOFError:
            break

        if user_input.lower() in {"exit", "quit"}:
            break

        context = retriever.retrieve(user_input, top_k=5)
        response = dispatch(user_input, context)
        citations = formatter.format_citations(context)

        print("\nContext:")
        print(citations or "(no context)")
        print("\nAssistant:")
        print(response)

        _log_interaction(log_path, user_input, context, response)

    print(f"Session log written to {log_path}")


def _log_interaction(
    log_path: Path, user_input: str, context: Iterable[RetrievedChunk], response: str
) -> None:
    payload = {
        "timestamp": dt.datetime.utcnow().isoformat() + "Z",
        "user_input": user_input,
        "context": [
            {
                "chunk_id": item.chunk.chunk_id,
                "metadata": item.chunk.metadata,
                "text": item.chunk.text,
                "score": item.score,
            }
            for item in context
        ],
        "response": response,
    }
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload))
        handle.write("\n")


def _load_corpus(file_path: str) -> List[dict]:
    with open(file_path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Chat interface with retrieval support")
    parser.add_argument("--corpus", required=True, help="Path to normalized corpus JSON file")
    args = parser.parse_args(argv)

    corpus = _load_corpus(args.corpus)
    retriever = Retriever.from_corpus(corpus)

    def echo_router(message: str, context: List[RetrievedChunk]) -> str:
        return f"Echo: {message}\nContext size: {len(context)}"

    run_chat_loop(retriever=retriever, router=echo_router)


if __name__ == "__main__":
    main()

