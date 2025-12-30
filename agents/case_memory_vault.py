"""Analyzer that maintains structured case memory and reminders."""
from __future__ import annotations

from typing import List

from .base import Analyzer, AnalysisRequest


class CaseMemoryVault(Analyzer):
    name = "case_memory_vault"
    prompt_template = (
        "Summarize key facts, actors, deadlines, and evidence locations for future recall."
    )
    guardrails = "Guardrail: preserve confidentiality, avoid speculative statements, and timestamp sources."

    def analyze(self, request: AnalysisRequest) -> List[str]:
        metadata_summary = (
            f"Stored metadata: {request.metadata!r}" if request.metadata else "No extra metadata supplied."
        )
        return [
            self.prompt_template,
            f"Case memory update: {request.content}",
            metadata_summary,
            "Organize entries by category (medical, correspondence, filings, timelines).",
            self.guardrails,
        ]
