"""High-level case operations for WCB Super Advocate."""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Iterable, List

from wcb_app.models import CaseState, Issue, TimelineEntry
from wcb_app.storage import save_case_state

logger = logging.getLogger(__name__)


def build_timeline(case_state: CaseState, entries: Iterable[TimelineEntry]) -> None:
    """Append timeline entries and persist."""
    new_entries = list(entries)
    case_state.timeline.extend(new_entries)
    save_case_state(case_state)
    logger.info("Added %s timeline entries", len(new_entries))


def build_issues(case_state: CaseState, issues: Iterable[Issue]) -> None:
    """Append issues and persist."""
    new_issues = list(issues)
    case_state.issues.extend(new_issues)
    save_case_state(case_state)
    logger.info("Added %s issues", len(new_issues))


def export_all(case_state: CaseState) -> Path:
    """Export timeline, issues, and a contradictions checklist."""
    exports_dir = Path(case_state.base_path) / "exports"
    exports_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")

    timeline_txt = exports_dir / f"timeline_{timestamp}.txt"
    timeline_json = exports_dir / f"timeline_{timestamp}.json"
    issues_txt = exports_dir / f"issues_{timestamp}.txt"
    issues_json = exports_dir / f"issues_{timestamp}.json"
    checklist_txt = exports_dir / f"contradictions_checklist_{timestamp}.txt"

    timeline_txt.write_text(_format_timeline_text(case_state.timeline), encoding="utf-8")
    timeline_json.write_text(json.dumps([entry.model_dump() for entry in case_state.timeline], indent=2), encoding="utf-8")

    issues_txt.write_text(_format_issues_text(case_state.issues), encoding="utf-8")
    issues_json.write_text(json.dumps([issue.model_dump() for issue in case_state.issues], indent=2), encoding="utf-8")

    checklist_txt.write_text(_build_checklist(case_state), encoding="utf-8")

    save_case_state(case_state)
    logger.info("Exported case package to %s", exports_dir)
    return exports_dir


def _format_timeline_text(timeline: List[TimelineEntry]) -> str:
    if not timeline:
        return "No timeline entries recorded yet."
    lines = ["Case Timeline:"]
    for entry in timeline:
        lines.append(f"- {entry.event_date}: {entry.description}")
    return "\n".join(lines)


def _format_issues_text(issues: List[Issue]) -> str:
    if not issues:
        return "No issues recorded yet."
    lines = ["Case Issues:"]
    for issue in issues:
        lines.append(f"- {issue.title}: {issue.detail}")
    return "\n".join(lines)


def _build_checklist(case_state: CaseState) -> str:
    """Build a gentle contradictions checklist."""
    lines = [
        "Contradictions Checklist (neutral language):",
        "- Compare decision dates against documented medical visits.",
        "- Confirm wage information matches employer records.",
        "- Verify return-to-work discussions align with correspondence.",
        "- Note any unclear statements to ask about (avoid accusations).",
        "",
        "Observed timeline entries:",
    ]
    lines.extend([f"* {entry.event_date}: {entry.description}" for entry in case_state.timeline])
    lines.append("")
    lines.append("Observed issues:")
    lines.extend([f"* {issue.title}: {issue.detail}" for issue in case_state.issues])
    lines.append("")
    lines.append("Reminder: This is not legal advice. Keep requests neutral and fact-based.")
    return "\n".join(lines)
