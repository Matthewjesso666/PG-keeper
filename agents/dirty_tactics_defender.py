"""Analyzer that defends against adversarial or obstructive tactics."""
from __future__ import annotations

from typing import List

from .base import Analyzer, AnalysisRequest


class DirtyTacticsDefender(Analyzer):
    name = "dirty_tactics_defender"
    prompt_template = (
        "Identify obstruction, delay, or intimidation tactics and suggest polite, documented responses."
    )
    guardrails = "Guardrail: encourage de-escalation and documentation rather than confrontation."

    def analyze(self, request: AnalysisRequest) -> List[str]:
        return [
            self.prompt_template,
            f"Potential tactics in: {request.content}",
            "Recommend responses that create a clear paper trail and preserve rights.",
            self.guardrails,
        ]
