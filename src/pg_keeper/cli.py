from __future__ import annotations

from pathlib import Path
from typing import List, Optional

import typer
from rich.console import Console

from .chatbot import chat as chat_with_context
from .config import Settings
from .drafting import draft_response
from .ingest import ingest_paths

app = typer.Typer(add_completion=False, no_args_is_help=True, help="PG Keeper CLI utilities.")
console = Console()


@app.command(help="Ingest documents into the vector store")
def ingest(
    paths: List[Path] = typer.Argument(..., exists=False, help="File or directory paths to ingest"),
    collection: str = typer.Option("case-vault", "--collection", "-c", help="Collection name"),
):
    settings = Settings.from_env()
    count = ingest_paths(paths, settings=settings, collection_name=collection)
    console.print(f"[bold cyan]Finished ingestion:[/] {count} documents")


@app.command(help="Chat over ingested context")
def chat(
    query: str = typer.Argument(..., help="Question about the WCB case"),
    collection: str = typer.Option("case-vault", "--collection", "-c", help="Collection name"),
    top_k: int = typer.Option(4, "--top-k", "-k", help="Number of context chunks to return"),
):
    settings = Settings.from_env()
    response = chat_with_context(query=query, settings=settings, collection_name=collection, top_k=top_k)
    console.print_json(data=response)


@app.command(help="Draft a response or appeal note")
def draft(
    prompt: str = typer.Argument(..., help="What to draft (e.g., appeal letter, follow-up email)"),
    tone: str = typer.Option("professional", help="Tone for the draft"),
    length: str = typer.Option("short", help="Length guidance"),
):
    settings = Settings.from_env()
    draft_text = draft_response(prompt=prompt, settings=settings, tone=tone, length=length)
    console.print(draft_text)


def main():
    app()


def pg_keeper_ingest():  # entrypoint convenience
    app(args=["ingest"])


def pg_keeper_chat():
    app(args=["chat"])


def pg_keeper_draft():
    app(args=["draft"])


if __name__ == "__main__":
    main()
