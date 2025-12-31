"""Case storage and state helpers."""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List

from wcb_app.models import CaseState, Document, Issue, TimelineEntry
from wcb_app.utils import DEFAULT_CASES_DIR, ensure_dir

logger = logging.getLogger(__name__)


def case_path(case_name: str, cases_dir: Path = DEFAULT_CASES_DIR) -> Path:
    """Return the path for a named case."""
    return cases_dir / case_name


def create_case(case_name: str, factual_only: bool = True) -> CaseState:
    """Initialize a new case folder and state."""
    base_path = case_path(case_name)
    imports_dir = base_path / "imports"
    exports_dir = base_path / "exports"
    policy_dir = base_path / "policy"
    notes_dir = base_path / "notes"

    for folder in [imports_dir, exports_dir, policy_dir, notes_dir]:
        ensure_dir(folder)

    state = CaseState(
        case_name=case_name,
        base_path=str(base_path),
        factual_only=factual_only,
    )
    save_case_state(state)
    logger.info("Created case '%s' at %s", case_name, base_path)
    return state


def save_case_state(case_state: CaseState) -> None:
    """Persist the case state to disk."""
    base_path = Path(case_state.base_path)
    ensure_dir(base_path)
    case_state.updated_at = datetime.utcnow()
    state_path = base_path / "case_state.json"
    state_path.write_text(
        json.dumps(case_state.model_dump(), indent=2, default=str),
        encoding="utf-8",
    )
    logger.info("Saved case state to %s", state_path)


def load_case_state(base_path: Path) -> CaseState:
    """Load a case state from disk."""
    state_path = base_path / "case_state.json"
    data = json.loads(state_path.read_text(encoding="utf-8"))
    state = CaseState.model_validate(data)
    logger.info("Loaded case state from %s", state_path)
    return state


def load_case(base_path: Path) -> CaseState:
    """Alias for loading a case to align with the public API."""
    return load_case_state(base_path)


def list_cases(cases_dir: Path = DEFAULT_CASES_DIR) -> List[str]:
    """List available case folders."""
    ensure_dir(cases_dir)
    return sorted(
        [p.name for p in cases_dir.iterdir() if p.is_dir() and (p / "case_state.json").exists()]
    )


def summarize_documents(documents: List[Document]) -> str:
    """Return a human-readable summary of documents."""
    if not documents:
        return "No documents imported yet."
    lines = []
    for doc in documents:
        label = f"{doc.filename} ({doc.doc_type})"
        status = "with extracted text" if doc.extracted_text_path else "imported"
        lines.append(f"- {label} [{status}]")
    return "\n".join(lines)


def summarize_timeline(timeline: List[TimelineEntry]) -> str:
    """Return a human-readable summary of the timeline."""
    if not timeline:
        return "No timeline entries yet."
    lines = [f"- {entry.event_date}: {entry.description}" for entry in timeline]
    return "\n".join(lines)


def summarize_issues(issues: List[Issue]) -> str:
    """Return a human-readable summary of issues."""
    if not issues:
        return "No issues recorded yet."
    lines = [f"- {issue.title}: {issue.detail}" for issue in issues]
    return "\n".join(lines)
