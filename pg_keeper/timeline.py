"""Deadline tracking for WCB cases."""
from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Iterable, List


@dataclass
class Deadline:
    title: str
    due: datetime
    notes: str | None = None

    @classmethod
    def from_dict(cls, data: dict) -> "Deadline":
        return cls(title=data["title"], due=datetime.fromisoformat(data["due"]), notes=data.get("notes"))


class Timeline:
    def __init__(self, storage_root: Path):
        self.storage_root = storage_root
        self.path = storage_root / "case_memory" / "deadlines.json"
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def _load(self) -> List[Deadline]:
        if not self.path.exists():
            return []
        with self.path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        return [Deadline.from_dict(item) for item in data]

    def _save(self, deadlines: Iterable[Deadline]) -> None:
        payload = [asdict(deadline) | {"due": deadline.due.isoformat()} for deadline in deadlines]
        with self.path.open("w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)

    def add(self, deadline: Deadline) -> None:
        deadlines = self._load()
        deadlines.append(deadline)
        self._save(deadlines)

    def upcoming(self, within_days: int = 14) -> List[Deadline]:
        now = datetime.utcnow()
        window_end = now + timedelta(days=within_days)
        return [d for d in self._load() if now <= d.due <= window_end]

    def list_all(self) -> List[Deadline]:
        return self._load()
