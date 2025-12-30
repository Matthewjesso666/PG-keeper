"""Route analysis requests to specialized analyzers and aggregate insights."""
from __future__ import annotations

import logging
from typing import Dict, Iterable, List, Sequence

from .appeal_strategist import AppealStrategist
from .base import AnalysisReport, AnalysisRequest, Analyzer, AnalyzerResult
from .case_memory_vault import CaseMemoryVault
from .dirty_tactics_defender import DirtyTacticsDefender
from .fairness_reviewer import FairnessReviewer
from .loophole_finder import LoopholeFinder

logger = logging.getLogger(__name__)


class AnalysisRouter:
    """Orchestrates analyzers based on the request type."""

    DEFAULT_ANALYZERS: Sequence[Analyzer] = (
        LoopholeFinder(),
        FairnessReviewer(),
        AppealStrategist(),
        DirtyTacticsDefender(),
        CaseMemoryVault(),
    )

    ROUTE_MAP: Dict[str, Sequence[str]] = {
        "loophole": (LoopholeFinder.name, DirtyTacticsDefender.name),
        "fairness": (FairnessReviewer.name, DirtyTacticsDefender.name),
        "appeal": (AppealStrategist.name, FairnessReviewer.name),
        "memory": (CaseMemoryVault.name,),
        "comprehensive": tuple(analyzer.name for analyzer in DEFAULT_ANALYZERS),
    }

    def __init__(self, analyzers: Sequence[Analyzer] | None = None) -> None:
        self.analyzers = list(analyzers) if analyzers else list(self.DEFAULT_ANALYZERS)
        self._analyzer_index: Dict[str, Analyzer] = {a.name: a for a in self.analyzers}

    def select_analyzers(self, request_type: str) -> List[Analyzer]:
        request_type = (request_type or "").lower()
        names = self.ROUTE_MAP.get(request_type, tuple(analyzer.name for analyzer in self.analyzers))
        selected = [self._analyzer_index[name] for name in names if name in self._analyzer_index]
        logger.debug("Selected analyzers for %s: %s", request_type, [a.name for a in selected])
        return selected

    def analyze(self, request: AnalysisRequest) -> AnalysisReport:
        analyzers = self.select_analyzers(request.request_type)
        results: List[AnalyzerResult] = []
        combined: List[str] = []

        for analyzer in analyzers:
            insights = analyzer.run(request)
            results.append(AnalyzerResult(analyzer=analyzer.name, insights=insights))
            combined.extend(insights)

        combined = self._merge_insights(combined)
        return AnalysisReport(
            request_type=request.request_type,
            results=results,
            combined_insights=combined,
        )

    @staticmethod
    def _merge_insights(insights: Iterable[str]) -> List[str]:
        """Deduplicate while preserving order."""

        seen = set()
        merged: List[str] = []
        for insight in insights:
            if insight not in seen:
                merged.append(insight)
                seen.add(insight)
        return merged
