"""Command-line entrypoints for PG Keeper."""
from __future__ import annotations

import argparse
from pathlib import Path

from datetime import datetime

from .config import load_config
from .pipeline import IngestionPipeline
from .timeline import Deadline, Timeline


def ingest_demo(text_file: Path, attachments: list[Path]) -> None:
    config = load_config()
    pipeline = IngestionPipeline(config)
    text = text_file.read_text(encoding="utf-8")
    pipeline.process_item(text=text, attachments=attachments, subject=text_file.stem, source=str(text_file))
    print(f"Ingested {text_file}")


def show_deadlines() -> None:
    config = load_config()
    timeline = Timeline(config.storage_root)
    for deadline in timeline.list_all():
        print(f"{deadline.due.date()} - {deadline.title} ({deadline.notes or ''})")


def add_deadline(title: str, due: str, notes: str | None) -> None:
    config = load_config()
    timeline = Timeline(config.storage_root)
    timeline.add(Deadline(title=title, due=datetime.fromisoformat(due), notes=notes))
    print("Deadline added.")


def main() -> None:
    parser = argparse.ArgumentParser(description="PG Keeper CLI")
    subparsers = parser.add_subparsers(dest="command")

    ingest_parser = subparsers.add_parser("ingest", help="Ingest a text file and optional attachments")
    ingest_parser.add_argument("text", type=Path, help="Path to text or email body file")
    ingest_parser.add_argument("attachments", nargs="*", type=Path, help="Attachment paths")

    deadline_parser = subparsers.add_parser("deadline", help="Add a deadline")
    deadline_parser.add_argument("title", help="Title of the deadline")
    deadline_parser.add_argument("due", help="Due date ISO format (YYYY-MM-DD)")
    deadline_parser.add_argument("--notes", help="Optional notes")

    subparsers.add_parser("deadlines", help="List deadlines")

    args = parser.parse_args()

    if args.command == "ingest":
        ingest_demo(args.text, args.attachments)
    elif args.command == "deadline":
        add_deadline(args.title, args.due, args.notes)
    elif args.command == "deadlines":
        show_deadlines()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
