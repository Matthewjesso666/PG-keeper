"""Specialized analysis agents for WCB case management."""
from __future__ import annotations

from dataclasses import dataclass
from types import SimpleNamespace
from typing import Iterable, List, Protocol

from openai import OpenAI
from langchain_core.documents import Document


@dataclass
class AgentResult:
    """Represents the output of a specialized agent."""

    name: str
    summary: str
    citations: List[str]


class ChatModel(Protocol):
    """Protocol for chat models used by specialized agents."""

    def __call__(self, messages: list[dict[str, str]]) -> object:
        """Invoke model and return an object exposing a `content` attribute."""


class OpenAIChatModel:
    """Minimal chat model wrapper around the OpenAI responses API."""

    def __init__(self, model_name: str = "gpt-4o-mini") -> None:
        self.model_name = model_name
        self.client = OpenAI()

    def __call__(self, messages: list[dict[str, str]]) -> object:
        response = self.client.responses.create(model=self.model_name, input=messages)
        return SimpleNamespace(content=response.output_text)


class BaseCaseAgent:
    """Base class for all case agents."""

    def __init__(self, *, model_name: str = "gpt-4o-mini", llm: ChatModel | None = None) -> None:
        self.llm = llm or OpenAIChatModel(model_name=model_name)

    def run(self, context: List[Document]) -> AgentResult:  # pragma: no cover - orchestrated externally
        raise NotImplementedError

    def _render(self, name: str, instructions: str, context: List[Document]) -> AgentResult:
        messages = [
            {"role": "system", "content": instructions},
            {
                "role": "user",
                "content": (
                    "Context documents:\n"
                    f"{[d.page_content for d in context]}\n"
                    "Provide a concise summary and list any citation IDs used."
                ),
            },
        ]
        response = self.llm(messages)
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


def draft_case_response(
    *,
    prompt: str,
    context: Iterable[Document],
    agent_results: Iterable[AgentResult],
    model_name: str = "gpt-4o-mini",
    llm: ChatModel | None = None,
) -> str:
    """Generate an outbound draft that references evidence and specialist recommendations."""

    effective_llm = llm or OpenAIChatModel(model_name=model_name)

    findings = "\n".join(f"- {item.name}: {item.summary}" for item in agent_results)
    context_text = "\n".join(
        f"- [{doc.metadata.get('id', 'unknown')}] {doc.page_content}" for doc in context
    )
    messages = [
        {
            "role": "system",
            "content": (
                "You are a case assistant writing concise, professional drafts for a WCB claimant. "
                "Always stay factual, cite referenced document IDs inline like [doc:123], and "
                "finish with a short 'Requested next actions' list."
            ),
        },
        {
            "role": "user",
            "content": (
                f"User goal:\n{prompt}\n\n"
                f"Specialist findings:\n{findings}\n\n"
                f"Case context:\n{context_text}"
            ),
        },
    ]
    return effective_llm(messages).content
