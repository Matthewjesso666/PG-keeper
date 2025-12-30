"""Shared analyzer abstractions and logging helpers."""
from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List

logger = logging.getLogger(__name__)


@dataclass
class AnalysisRequest:
    """Input sent to analyzers."""

    request_type: str
    content: str
    metadata: Dict[str, str] = field(default_factory=dict)


@dataclass
class AnalyzerResult:
    """Container for an individual analyzer's insights."""

    analyzer: str
    insights: List[str]


@dataclass
class AnalysisReport:
    """Aggregated analyzer output."""

    request_type: str
    results: List[AnalyzerResult]
    combined_insights: List[str]

    def as_dict(self) -> Dict[str, object]:
        return {
            "request_type": self.request_type,
            "results": [result.__dict__ for result in self.results],
            "combined_insights": list(self.combined_insights),
        }


class Analyzer(ABC):
    """Analyzer contract for specialized modules."""

    name: str = "analyzer"

    def __init__(self) -> None:
        self.logger = logging.getLogger(self.name)

    @abstractmethod
    def analyze(self, request: AnalysisRequest) -> List[str]:
        """Analyze the request and return ordered insights."""

    def run(self, request: AnalysisRequest) -> List[str]:
        """Wrapper that adds logging around :meth:`analyze`."""

        self.logger.info("Analyzing %s request", request.request_type)
        insights = self.analyze(request)
        self.logger.debug("%s produced %d insights", self.name, len(insights))
        return insights
