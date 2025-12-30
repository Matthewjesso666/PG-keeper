"""Analyzer that surfaces procedural loopholes and process gaps."""
from __future__ import annotations

from typing import List

from .base import Analyzer, AnalysisRequest


class LoopholeFinder(Analyzer):
    name = "loophole_finder"
    prompt_template = (
        "Identify procedural gaps or overlooked policies that support the "
        "claimant. Focus on compliance-friendly suggestions and cite safe "
        "documentation tactics."
    )

    guardrails = (
        "Guardrail: stay within legal and ethical bounds, avoid proposing anything "
        "that obstructs legitimate reviews."
    )

    def analyze(self, request: AnalysisRequest) -> List[str]:
        return [
            self.prompt_template,
            f"Request focus: {request.content}",
            self.guardrails,
            "Deliver concise action items that can be evidenced with documents or timelines.",
        ]
