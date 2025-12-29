"""Specialized analysis agents for WCB case management."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List

from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema import Document


@dataclass
class AgentResult:
    """Represents the output of a specialized agent."""

    name: str
    summary: str
    citations: List[str]


class BaseCaseAgent:
    """Base class for all case agents."""

    def __init__(self, *, model_name: str = "gpt-4o-mini") -> None:
        self.llm = ChatOpenAI(model_name=model_name)

    def run(self, context: List[Document]) -> AgentResult:  # pragma: no cover - orchestrated externally
        raise NotImplementedError

    def _render(self, name: str, instructions: str, context: List[Document]) -> AgentResult:
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    instructions,
                ),
                (
                    "human",
                    "Context documents:\n{context}\nProvide a concise summary and list any citation IDs used.",
                ),
            ]
        )
        rendered = prompt.format_prompt(context=[d.page_content for d in context]).to_messages()
        response = self.llm(rendered)
        return AgentResult(name=name, summary=response.content, citations=[d.metadata.get("id", "unknown") for d in context])


class LoopholeFinder(BaseCaseAgent):
    """Searches for procedural or regulatory weaknesses."""

    def run(self, context: List[Document]) -> AgentResult:
        instructions = (
            "You are the Loophole Finder. Identify procedural gaps, missed deadlines, or policy "
            "exceptions that could benefit the claimant. Be precise and list actionable steps."
        )
        return self._render("Loophole Finder", instructions, context)


class FairnessReviewExpert(BaseCaseAgent):
    """Checks fairness and adherence to policy."""

    def run(self, context: List[Document]) -> AgentResult:
        instructions = (
            "You are the Fairness Review Expert. Evaluate whether decisions respect WCB policies "
            "and fairness principles. Flag inconsistencies and suggest remedies."
        )
        return self._render("Fairness Review Expert", instructions, context)


class AppealStrategist(BaseCaseAgent):
    """Plans appeal strategies based on current evidence."""

    def run(self, context: List[Document]) -> AgentResult:
        instructions = (
            "You are the Appeal Strategist. Draft appeal angles, evidence needs, and timelines. "
            "Outline the strongest arguments and required exhibits."
        )
        return self._render("Appeal Strategist", instructions, context)


class DirtyTacticsDefender(BaseCaseAgent):
    """Identifies and mitigates adversarial tactics."""

    def run(self, context: List[Document]) -> AgentResult:
        instructions = (
            "You are the Dirty Tactics Defender. Detect bad-faith tactics, information asymmetry, "
            "or procedural barriers. Provide countermeasures and escalation paths."
        )
        return self._render("Dirty Tactics Defender", instructions, context)


class CaseMemoryVault(BaseCaseAgent):
    """Maintains a persistent summary of case history."""

    def run(self, context: List[Document]) -> AgentResult:
        instructions = (
            "You are the Case Memory/Vault. Produce a crisp timeline and key decisions with "
            "citations. Highlight items requiring follow-up."
        )
        return self._render("Case Memory/Vault", instructions, context)
