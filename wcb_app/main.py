"""Typer CLI entrypoint for WCB Super Advocate."""

import logging
from importlib import metadata
import platform
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import typer
from rich.console import Console
from rich.table import Table

from wcb_app import __version__
from wcb_app.drafts import generate_draft
from wcb_app.extraction import DOCUMENT_TYPES, import_document
from wcb_app.models import CaseState, Issue, TimelineEntry
from wcb_app.operations import build_issues, build_timeline, export_all
from wcb_app.storage import create_case, list_cases, load_case_state, summarize_documents, summarize_issues, summarize_timeline
from wcb_app.utils import DEFAULT_CASES_DIR, setup_logging

app = typer.Typer(add_completion=False, help="WCB Super Advocate - offline-first helper")
console = Console()
logger = logging.getLogger(__name__)


def run_wizard() -> None:
    """Interactive beginner-friendly wizard."""
    setup_logging()
    console.print("[bold cyan]Welcome to WCB Super Advocate (offline-first)[/bold cyan]")
    console.print("This helper keeps everything local and avoids the internet.\n")
    case_state: Optional[CaseState] = None
    DEFAULT_CASES_DIR.mkdir(parents=True, exist_ok=True)

    while True:
        if case_state is None:
            choice = _choose_option(
                "What would you like to do?",
                [
                    "Start new case",
                    "Open existing case",
                    "Diagnostics (environment info)",
                    "Exit",
                ],
            )
            if choice == 1:
                case_state = _start_new_case()
            elif choice == 2:
                case_state = _open_case()
            elif choice == 3:
                _show_diagnostics()
            else:
                console.print("Goodbye. Remember to keep your files backed up locally.")
                break
        else:
            console.print(f"\n[bold]Current case:[/bold] {case_state.case_name}")
            choice = _choose_option(
                "Select a step:",
                [
                    "Import documents",
                    "Build timeline",
                    "Build issues list",
                    "Draft appeal/review/disclosure letter",
                    "Export package (TXT + DOCX + JSON)",
                    "View case summary",
                    "Switch case",
                    "Diagnostics",
                    "Exit",
                ],
            )
            if choice == 1:
                _import_flow(case_state)
            elif choice == 2:
                _timeline_flow(case_state)
            elif choice == 3:
                _issues_flow(case_state)
            elif choice == 4:
                _draft_flow(case_state)
            elif choice == 5:
                _export_flow(case_state)
            elif choice == 6:
                _show_case_summary(case_state)
            elif choice == 7:
                case_state = None
            elif choice == 8:
                _show_diagnostics()
            else:
                console.print("Goodbye. You can resume by running the app again.")
                break


def _start_new_case() -> CaseState:
    case_name = typer.prompt("Enter a case name").strip()
    safe_name = case_name.replace("\\", "_").replace("/", "_").replace(" ", "_")
    factual_only = typer.confirm("Enable Factual-Only Mode? (recommended)", default=True)
    case_state = create_case(safe_name, factual_only=factual_only)
    console.print(f"Created case at {case_state.base_path}")
    console.print("Next step: import documents.")
    typer.prompt("Press Enter to continue")
    return case_state


def _open_case() -> Optional[CaseState]:
    available = list_cases()
    if not available:
        console.print("No cases found yet. Start a new case first.")
        typer.prompt("Press Enter to continue")
        return None

    console.print("\nAvailable cases:")
    for idx, name in enumerate(available, start=1):
        console.print(f"{idx}. {name}")

    selection = typer.prompt("Enter the number of the case to open")
    try:
        index = int(selection) - 1
        if index < 0 or index >= len(available):
            raise ValueError
    except ValueError:
        console.print("Invalid choice. Returning to menu.")
        return None

    base_path = DEFAULT_CASES_DIR / available[index]
    case_state = load_case_state(base_path)
    console.print(f"Opened case '{case_state.case_name}'.")
    typer.prompt("Press Enter to continue")
    return case_state


def _import_flow(case_state: CaseState) -> None:
    console.print("\nImport a document (PDF/DOCX/TXT). Files will be copied into the case folder.")
    path_input = typer.prompt("Enter the full path to the document")
    doc_type = _choose_doc_type()
    document, message = import_document(case_state, Path(path_input), doc_type)
    console.print(message)
    if document:
        console.print(f"Stored as: {document.stored_path}")
    console.print("Next step: build the timeline or add issues.")
    typer.prompt("Press Enter to continue")


def _timeline_flow(case_state: CaseState) -> None:
    console.print("\nBuild the case timeline. Keep entries short and factual.")
    _show_existing_timeline(case_state)
    new_entries: List[TimelineEntry] = []
    while True:
        date_value = typer.prompt("Event date (YYYY-MM-DD, leave blank to finish)", default="")
        if not date_value.strip():
            break
        description = typer.prompt("Brief description of the event")
        doc_id = _choose_document(case_state, allow_skip=True)
        new_entries.append(
            TimelineEntry(
                event_date=date_value.strip(),
                description=description.strip(),
                source_document_id=doc_id,
            )
        )
    if new_entries:
        build_timeline(case_state, new_entries)
        console.print(f"Added {len(new_entries)} timeline entries.")
    else:
        console.print("No new entries added.")
    console.print("Next step: add issues or generate a draft.")
    typer.prompt("Press Enter to continue")


def _issues_flow(case_state: CaseState) -> None:
    console.print("\nList the issues you want to flag (neutral language).")
    _show_existing_issues(case_state)
    new_issues: List[Issue] = []
    while True:
        title = typer.prompt("Issue title (leave blank to finish)", default="")
        if not title.strip():
            break
        detail = typer.prompt("What is the concern? Use neutral language.")
        doc_id = _choose_document(case_state, allow_skip=True)
        new_issues.append(
            Issue(title=title.strip(), detail=detail.strip(), related_document_id=doc_id)
        )
    if new_issues:
        build_issues(case_state, new_issues)
        console.print(f"Added {len(new_issues)} issues.")
    else:
        console.print("No new issues added.")
    console.print("Next step: generate a draft or export package.")
    typer.prompt("Press Enter to continue")


def _draft_flow(case_state: CaseState) -> None:
    console.print("\nDraft options use local templates and stay factual.")
    choice = _choose_option(
        "Choose a draft to generate",
        [
            "Appeal/Review submission skeleton",
            "Fairness Review letter skeleton",
            "Disclosure request letter skeleton",
            "Cancel",
        ],
    )
    mapping = {1: "appeal", 2: "fairness", 3: "disclosure"}
    draft_type = mapping.get(choice)
    if not draft_type:
        console.print("Cancelled. No draft created.")
        return
    record = generate_draft(case_state, draft_type)
    if record:
        console.print(f"Draft saved to:\n- {record.txt_path}\n- {record.docx_path}")
    else:
        console.print("Could not generate the draft.")
    console.print("Next step: review the draft and export the package.")
    typer.prompt("Press Enter to continue")


def _export_flow(case_state: CaseState) -> None:
    path = export_all(case_state)
    console.print(f"Exported timeline, issues, and checklist to {path}")
    console.print("Next step: review files in the exports folder.")
    typer.prompt("Press Enter to continue")


def _show_case_summary(case_state: CaseState) -> None:
    console.print("\n[bold]Case summary[/bold]")
    console.print(f"Case name: {case_state.case_name}")
    console.print(f"Location: {case_state.base_path}")
    console.print(f"Factual-Only Mode: {'ON' if case_state.factual_only else 'OFF'}")
    console.print("\nDocuments:")
    console.print(summarize_documents(case_state.documents))
    console.print("\nTimeline:")
    console.print(summarize_timeline(case_state.timeline))
    console.print("\nIssues:")
    console.print(summarize_issues(case_state.issues))
    console.print("\nNext step: import documents or draft a letter.")
    typer.prompt("Press Enter to continue")


def _show_existing_timeline(case_state: CaseState) -> None:
    if not case_state.timeline:
        console.print("No timeline entries yet.")
        return
    table = Table(title="Existing timeline")
    table.add_column("Date")
    table.add_column("Description")
    for entry in case_state.timeline:
        table.add_row(entry.event_date, entry.description)
    console.print(table)


def _show_existing_issues(case_state: CaseState) -> None:
    if not case_state.issues:
        console.print("No issues recorded yet.")
        return
    table = Table(title="Existing issues")
    table.add_column("Title")
    table.add_column("Detail")
    for issue in case_state.issues:
        table.add_row(issue.title, issue.detail)
    console.print(table)


def _choose_option(prompt_text: str, options: List[str]) -> int:
    console.print(f"\n{prompt_text}")
    for idx, opt in enumerate(options, start=1):
        console.print(f"{idx}. {opt}")
    while True:
        selection = typer.prompt("Enter a number")
        try:
            value = int(selection)
            if 1 <= value <= len(options):
                return value
        except ValueError:
            pass
        console.print("Please choose a listed number.")


def _choose_doc_type() -> str:
    console.print("Select a tag for this document (or press Enter for 'other').")
    for idx, doc_type in enumerate(DOCUMENT_TYPES, start=1):
        console.print(f"{idx}. {doc_type}")
    selection = typer.prompt("Enter a number", default="")
    try:
        index = int(selection) - 1
        if 0 <= index < len(DOCUMENT_TYPES):
            return DOCUMENT_TYPES[index]
    except ValueError:
        pass
    return "other"


def _choose_document(case_state: CaseState, allow_skip: bool = False) -> Optional[str]:
    """Return a document ID or None."""
    if not case_state.documents:
        return None
    console.print("Link to a document? Choose a number or press Enter to skip.")
    for idx, doc in enumerate(case_state.documents, start=1):
        console.print(f"{idx}. {doc.filename} ({doc.doc_type})")
    if allow_skip:
        console.print("0. Skip linking")
    selection = typer.prompt("Enter choice", default="")
    if selection.strip() == "" or selection == "0":
        return None
    try:
        index = int(selection) - 1
        if 0 <= index < len(case_state.documents):
            return case_state.documents[index].id
    except ValueError:
        pass
    console.print("No document linked.")
    return None


def _show_diagnostics() -> None:
    console.print("\n[bold]Diagnostics[/bold]")
    console.print(f"Python: {platform.python_version()}")
    console.print(f"Platform: {platform.platform()}")
    console.print(f"App version: {__version__}")
    console.print(f"Cases directory: {DEFAULT_CASES_DIR}")
    deps = ["typer", "rich", "pydantic", "python-docx", "pypdf", "jinja2", "PyInstaller"]
    for dep in deps:
        version = _get_dep_version(dep)
        console.print(f"- {dep}: {version}")
    typer.prompt("Press Enter to continue")


def _get_dep_version(package_name: str) -> str:
    try:
        return metadata.version(package_name)
    except metadata.PackageNotFoundError:
        return "not installed"


@app.command()
def wizard() -> None:
    """Launch the guided wizard."""
    run_wizard()


@app.command()
def diagnostics() -> None:
    """Show environment diagnostics."""
    setup_logging()
    _show_diagnostics()


if __name__ == "__main__":
    app()
