"""Draft generation for WCB Super Advocate."""

import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from docx import Document as DocxDocument
from jinja2 import Environment, FileSystemLoader, select_autoescape

from wcb_app.models import CaseState, DraftRecord
from wcb_app.storage import save_case_state
from wcb_app.utils import get_resource_path

logger = logging.getLogger(__name__)

TEMPLATE_FILES = {
    "appeal": "appeal_submission.j2",
    "fairness": "fairness_review.j2",
    "disclosure": "disclosure_request.j2",
}


def _load_template(template_name: str):
    """Return a Jinja2 template from the templates directory."""
    templates_dir = get_resource_path("templates")
    env = Environment(
        loader=FileSystemLoader(str(templates_dir)),
        autoescape=select_autoescape(),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    return env.get_template(template_name)


def gather_policy_snippets(policy_dir: Path) -> List[str]:
    """Read policy text snippets from the case policy folder."""
    if not policy_dir.exists():
        return []

    snippets: List[str] = []
    for path in sorted(policy_dir.glob("*.txt")):
        try:
            snippets.append(f"{path.name}: {path.read_text(encoding='utf-8').strip()}")
        except Exception as exc:  # noqa: BLE001
            logger.warning("Could not read policy file %s: %s", path, exc)
    return snippets


def generate_draft(case_state: CaseState, draft_type: str) -> Optional[DraftRecord]:
    """Generate both TXT and DOCX drafts."""
    template_file = TEMPLATE_FILES.get(draft_type)
    if not template_file:
        logger.error("Unknown draft type: %s", draft_type)
        return None

    template = _load_template(template_file)
    context = _build_context(case_state)
    rendered_text = template.render(**context)

    exports_dir = Path(case_state.base_path) / "exports"
    exports_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")

    txt_path = exports_dir / f"{draft_type}_draft_{timestamp}.txt"
    txt_path.write_text(rendered_text, encoding="utf-8")

    docx_path = exports_dir / f"{draft_type}_draft_{timestamp}.docx"
    _write_docx(rendered_text, docx_path)

    record = DraftRecord(
        draft_type=draft_type,
        txt_path=str(txt_path),
        docx_path=str(docx_path),
    )
    case_state.drafts.append(record)
    save_case_state(case_state)
    logger.info("Generated %s draft at %s", draft_type, exports_dir)
    return record


def _build_context(case_state: CaseState) -> Dict[str, object]:
    """Build the context dict used by Jinja templates."""
    policy_dir = Path(case_state.base_path) / "policy"
    policy_snippets = gather_policy_snippets(policy_dir)
    if not policy_snippets:
        policy_snippets = ["Policy source not provided yet."]

    context = {
        "case_name": case_state.case_name,
        "documents": case_state.documents,
        "timeline": case_state.timeline,
        "issues": case_state.issues,
        "policy_snippets": policy_snippets,
        "factual_only": case_state.factual_only,
        "disclaimer": (
            "This helper does not provide legal advice. "
            "Review all content before sending and keep language neutral."
        ),
    }
    return context


def _write_docx(text: str, output_path: Path) -> None:
    """Write the draft text to a DOCX file."""
    doc = DocxDocument()
    for block in text.split("\n"):
        doc.add_paragraph(block)
    doc.save(output_path)
