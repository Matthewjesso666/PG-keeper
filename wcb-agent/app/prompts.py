"""Prompt configuration loader for the WCB agent."""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import TypedDict


class PromptConfig(TypedDict):
    system_prompt: str
    capabilities_prompt: str
    behavior_prompt: str
    constraints_prompt: str


@lru_cache()
def get_prompts() -> PromptConfig:
    """Load immutable prompt sections from the config file."""

    prompts_path = Path(__file__).with_name("prompts.json")
    raw = json.loads(prompts_path.read_text(encoding="utf-8"))
    return PromptConfig(
        system_prompt=raw["system_prompt"],
        capabilities_prompt=raw["capabilities_prompt"],
        behavior_prompt=raw["behavior_prompt"],
        constraints_prompt=raw["constraints_prompt"],
    )


def build_base_system_prompt() -> str:
    """Combine prompt sections into a single system message."""

    prompts = get_prompts()
    return "\n\n".join(
        [
            prompts["system_prompt"],
            prompts["capabilities_prompt"],
            prompts["behavior_prompt"],
            prompts["constraints_prompt"],
        ]
    )
