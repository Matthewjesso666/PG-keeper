from __future__ import annotations

import sys
from pathlib import Path

from langchain_core.documents import Document

sys.path.append(str(Path(__file__).resolve().parents[1] / "wcb-agent"))

from app.agents.analysis import AgentResult, draft_case_response
from app.routers.cases import _build_documents_from_gmail, _categorize_text, _extract_gmail_body_text


class _FakeResponse:
    def __init__(self, content: str) -> None:
        self.content = content


class _FakeLlm:
    def __call__(self, _messages: list) -> _FakeResponse:
        return _FakeResponse("Draft generated")


def test_extracts_and_categorizes_gmail_body() -> None:
    message = {
        "id": "abc",
        "snippet": "appeal deadline",
        "payload": {
            "headers": [
                {"name": "Subject", "value": "WCB appeal needed"},
                {"name": "From", "value": "board@example.com"},
            ],
            "body": {"data": "SGVsbG8gd29ybGQ="},
        },
    }

    docs = _build_documents_from_gmail([message])

    assert docs[0].metadata["id"] == "abc"
    assert docs[0].metadata["source"] == "gmail"
    assert docs[0].metadata["category"] == "appeal"
    assert "Hello world" in docs[0].page_content


def test_body_extraction_from_parts() -> None:
    payload = {
        "parts": [
            {"mimeType": "text/plain", "body": {"data": "RGVhZGxpbmUgaXMgdG9tb3Jyb3c="}},
        ]
    }

    assert _extract_gmail_body_text(payload) == "Deadline is tomorrow"
    assert _categorize_text("Payment benefit update") == "finance"


def test_draft_case_response_returns_model_output() -> None:
    result = draft_case_response(
        prompt="Draft a follow-up",
        context=[Document(page_content="Decision letter", metadata={"id": "doc-1"})],
        agent_results=[AgentResult(name="Loophole Finder", summary="Use policy X", citations=["doc-1"])],
        llm=_FakeLlm(),
    )

    assert result == "Draft generated"
