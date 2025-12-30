import logging
import sys
from pathlib import Path

import pytest

sys.path.append(str(Path(__file__).resolve().parents[1]))

from agents import (
    AnalysisRequest,
    AnalysisRouter,
    AppealStrategist,
    CaseMemoryVault,
    DirtyTacticsDefender,
    FairnessReviewer,
    LoopholeFinder,
)


@pytest.fixture(autouse=True)
def configure_logging(caplog):
    caplog.set_level(logging.DEBUG)


def test_routes_specific_request_types():
    router = AnalysisRouter()

    loophole_selected = [a.name for a in router.select_analyzers("loophole")]
    assert LoopholeFinder.name in loophole_selected
    assert DirtyTacticsDefender.name in loophole_selected
    assert FairnessReviewer.name not in loophole_selected

    fairness_selected = [a.name for a in router.select_analyzers("fairness")]
    assert fairness_selected == [FairnessReviewer.name, DirtyTacticsDefender.name]

    memory_selected = [a.name for a in router.select_analyzers("memory")]
    assert memory_selected == [CaseMemoryVault.name]


def test_unknown_type_defaults_to_all_analyzers():
    router = AnalysisRouter()

    all_analyzer_names = {analyzer.name for analyzer in router.analyzers}
    selected = {a.name for a in router.select_analyzers("unexpected")}

    assert selected == all_analyzer_names


def test_aggregates_insights_without_duplicates():
    router = AnalysisRouter()
    request = AnalysisRequest(request_type="appeal", content="Missed deadline", metadata={"source": "email"})

    report = router.analyze(request)

    analyzer_names = [result.analyzer for result in report.results]
    assert analyzer_names == [AppealStrategist.name, FairnessReviewer.name]

    # Combined insights preserve order and drop duplicates
    flattened = [insight for result in report.results for insight in result.insights]
    assert len(report.combined_insights) <= len(flattened)
    assert report.combined_insights[0] == flattened[0]
    assert len(report.combined_insights) == len(set(report.combined_insights))

    assert report.as_dict()["request_type"] == "appeal"
