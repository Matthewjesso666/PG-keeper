"""Analyzer that drafts appeal strategies and deadlines."""
from __future__ import annotations

from typing import List

from .base import Analyzer, AnalysisRequest


class AppealStrategist(Analyzer):
    name = "appeal_strategist"
    prompt_template = (
        "Outline appeal angles, evidence priorities, and filing deadlines for the WCB case."
    )
    guardrails = "Guardrail: avoid legal advice; suggest options for claimant review with counsel."

    def analyze(self, request: AnalysisRequest) -> List[str]:
        return [
            self.prompt_template,
            f"Appeal scenario: {request.content}",
            "List critical dates and responsible parties for each action.",
            self.guardrails,
        ]
