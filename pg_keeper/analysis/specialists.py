"""Specialized GPT modules used by the agent."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List

from pg_keeper.llm import LLMClient
from pg_keeper.models import Document, SpecialistFinding


@dataclass
class Specialist:
    name: str
    objective: str
    llm: LLMClient

    def analyze(self, documents: Iterable[Document]) -> SpecialistFinding:
        prompt = self._build_prompt(documents)
        output = self.llm.complete(prompt, system=self.objective)
        return self._parse_output(output)

    def _build_prompt(self, documents: Iterable[Document]) -> str:
        bullet_points = []
        for doc in documents:
            bullet_points.append(f"- {doc.title} ({doc.category}): {doc.content[:280]}")
        return "\n".join(
            [
                "You are given key case documents. Provide a concise analysis with risks, opportunities, and recommended actions.",
                "Documents:",
                *bullet_points,
            ]
        )

    def _parse_output(self, output: str) -> SpecialistFinding:
        sections = {"risks": [], "opportunities": [], "actions": []}
        current = None
        for line in output.splitlines():
            lowered = line.lower()
            if "risk" in lowered:
                current = "risks"
            elif "opportunit" in lowered:
                current = "opportunities"
            elif "action" in lowered or "recommend" in lowered:
                current = "actions"
            elif line.strip().startswith("-") and current:
                sections[current].append(line.strip("- "))
        return SpecialistFinding(
            specialist=self.name,
            summary=output.strip(),
            risks=sections["risks"],
            opportunities=sections["opportunities"],
            recommended_actions=sections["actions"],
        )


@dataclass
class LoopholeFinder(Specialist):
    def __init__(self, llm: LLMClient):
        super().__init__(
            name="Loophole Finder",
            objective="Find exploitable procedural or legal gaps that could benefit the claimant.",
            llm=llm,
        )


@dataclass
class FairnessReviewExpert(Specialist):
    def __init__(self, llm: LLMClient):
        super().__init__(
            name="Fairness Review Expert",
            objective="Identify fairness issues, due process violations, or inconsistent handling.",
            llm=llm,
        )


@dataclass
class AppealStrategist(Specialist):
    def __init__(self, llm: LLMClient):
        super().__init__(
            name="Appeal Strategist",
            objective="Design the best appeal strategy with deadlines, filings, and evidence needs.",
            llm=llm,
        )


@dataclass
class DirtyTacticsDefender(Specialist):
    def __init__(self, llm: LLMClient):
        super().__init__(
            name="Dirty Tactics Defender",
            objective="Detect adversarial tactics or misrepresentations and propose counter-moves.",
            llm=llm,
        )


@dataclass
class CaseMemoryVault(Specialist):
    def __init__(self, llm: LLMClient):
        super().__init__(
            name="Case Memory Vault",
            objective="Maintain a structured memory of the case with timelines and key facts.",
            llm=llm,
        )

    def _build_prompt(self, documents: Iterable[Document]) -> str:  # type: ignore[override]
        bullet_points = []
        for doc in documents:
            bullet_points.append(
                f"- {doc.title} | {doc.category} | {doc.metadata.get('from', 'unknown sender')} | {doc.content[:280]}"
            )
        return "\n".join(
            [
                "Summarize the case timeline and critical facts. Identify missing information.",
                "Evidence notes:",
                *bullet_points,
            ]
        )
