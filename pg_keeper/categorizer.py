"""Heuristic categorizer for WCB documents."""
from __future__ import annotations

from collections.abc import Iterable

CATEGORIES = {
    "wage": ["wage", "earning", "salary", "income"],
    "medical_evidence": ["medical", "doctor", "clinic", "assessment", "MRI", "x-ray", "physio"],
    "procedural_fairness": ["fairness", "notice", "opportunity", "timeline", "procedural"],
    "policy": ["policy", "guideline", "act", "regulation", "wcb.ab.ca"],
    "appeal": ["appeal", "appeals commission", "hearing", "decision"],
    "communications": ["email", "correspondence", "letter", "submission"],
}


def categorize(text: str) -> str:
    lowered = text.lower()
    for category, keywords in CATEGORIES.items():
        if any(word in lowered for word in keywords):
            return category
    return "uncategorized"


def categories() -> Iterable[str]:
    return CATEGORIES.keys()
