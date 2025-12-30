"""LLM client abstraction for PG-keeper."""
from __future__ import annotations

import importlib.util
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Iterable, Optional


class LLMClient(ABC):
    @abstractmethod
    def complete(self, prompt: str, *, system: Optional[str] = None) -> str:
        raise NotImplementedError


@dataclass
class EchoLLMClient(LLMClient):
    """LLM stub that echoes the prompt for offline validation."""

    def complete(self, prompt: str, *, system: Optional[str] = None) -> str:  # noqa: D401
        prefix = f"[{system}] " if system else ""
        return f"{prefix}{prompt.strip()}"


@dataclass
class OpenAILLMClient(LLMClient):
    model: str

    def _ensure_dependencies(self) -> None:
        if importlib.util.find_spec("openai") is None:
            raise ImportError("openai package is required to call OpenAI models")

    def complete(self, prompt: str, *, system: Optional[str] = None) -> str:  # noqa: D401
        self._ensure_dependencies()
        import openai  # type: ignore

        client = openai.OpenAI()
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        response = client.chat.completions.create(model=self.model, messages=messages)
        return response.choices[0].message.content or ""
