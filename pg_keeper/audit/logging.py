"""Audit logging utilities for recording actions."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


@dataclass
class AuditRecord:
    action: str
    input_data: Dict[str, Any]
    output_data: Dict[str, Any]
    source_id: str
    timestamp: datetime

    def to_dict(self) -> Dict[str, Any]:
        return {
            "action": self.action,
            "input": self.input_data,
            "output": self.output_data,
            "source_id": self.source_id,
            "timestamp": self.timestamp.isoformat(),
        }


class AuditLogger:
    """Simple in-memory logger for tracking inputs/outputs per action."""

    def __init__(self, clock: Optional[callable] = None) -> None:
        self._clock = clock or (lambda: datetime.now(timezone.utc))
        self.records: List[AuditRecord] = []

    def log_action(
        self,
        action: str,
        input_data: Dict[str, Any],
        output_data: Dict[str, Any],
        source_id: str,
    ) -> AuditRecord:
        timestamp = self._clock()
        record = AuditRecord(
            action=action,
            input_data=input_data,
            output_data=output_data,
            source_id=source_id,
            timestamp=timestamp,
        )
        self.records.append(record)
        return record

    def latest(self) -> Optional[AuditRecord]:
        return self.records[-1] if self.records else None
