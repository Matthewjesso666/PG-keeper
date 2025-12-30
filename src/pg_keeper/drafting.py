from __future__ import annotations

from typing import List, Optional

from .config import Settings


def draft_response(prompt: str, settings: Settings, tone: str = "professional", length: str = "short") -> str:
    guidance: List[str] = [
        "Summarize the claim facts in a neutral tone.",
        "Highlight fairness considerations and applicable WCB policy references.",
        "Suggest follow-up requests for missing evidence.",
        "Close with a clear next action and deadline.",
    ]

    return (
        f"Model: {settings.model_name}\n"
        f"Requested tone: {tone}; length: {length}\n\n"
        f"Prompt: {prompt}\n\n"
        "Draft outline:\n- " + "\n- ".join(guidance)
    )
