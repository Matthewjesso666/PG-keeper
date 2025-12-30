"""Analyzer that evaluates fairness and due process."""
from __future__ import annotations

from typing import List

from .base import Analyzer, AnalysisRequest


class FairnessReviewer(Analyzer):
    name = "fairness_reviewer"
    prompt_template = (
        "Check for bias, due-process violations, and missing claimant voice. "
        "Highlight requirements for balanced review and transparent communication."
    )

    guardrails = "Guardrail: flag remedies that promote equitable treatment without escalating conflict."

    def analyze(self, request: AnalysisRequest) -> List[str]:
        metadata_note = (
            f"Metadata considered: {', '.join(sorted(request.metadata)) or 'none provided'}."
        )
        return [
            self.prompt_template,
            f"Fairness concerns in: {request.content}",
            metadata_note,
            self.guardrails,
            "Provide checklist-style recommendations that are easy to verify.",
        ]
