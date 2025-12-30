from pg_keeper.analysis.specialists import LoopholeFinder
from pg_keeper.llm import EchoLLMClient
from pg_keeper.models import Document, SourceType
from pg_keeper.pipeline import CaseAgent
from pg_keeper.config import AgentConfig


def sample_documents():
    return [
        Document(
            identifier="doc1",
            title="Email about claim delay",
            source=SourceType.MANUAL,
            content="Email thread showing delay and unfair processing",
        ),
        Document(
            identifier="doc2",
            title="Medical note",
            source=SourceType.MANUAL,
            content="Doctor explains injury and recommends therapy",
        ),
    ]


def test_specialist_builds_findings_without_llm_call():
    llm = EchoLLMClient()
    specialist = LoopholeFinder(llm)
    finding = specialist.analyze(sample_documents())
    assert finding.specialist == "Loophole Finder"
    assert "Documents:" in finding.summary


def test_agent_drafts_response_offline():
    agent = CaseAgent(config=AgentConfig(dry_run=True), llm_client=EchoLLMClient())
    indexed = agent.index_documents(sample_documents())
    findings = agent.run_specialists([record.document for record in indexed])
    draft = agent.draft_response(findings)
    assert "Case update" in draft.subject
    assert draft.body.startswith("Dear")
