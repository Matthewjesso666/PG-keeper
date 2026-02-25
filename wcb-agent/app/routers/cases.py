"""API routes for managing WCB case data, analysis, and drafting."""
from __future__ import annotations

import base64
import re
from typing import List
from uuid import uuid4

from fastapi import APIRouter, Depends
from langchain_core.documents import Document
from pydantic import BaseModel, Field

from app.agents.analysis import (
    AppealStrategist,
    CaseMemoryVault,
    DirtyTacticsDefender,
    FairnessReviewExpert,
    LoopholeFinder,
    draft_case_response,
)
from app.config import Settings, get_settings
from app.indexing.vector_store import build_index
from app.services.drive_client import DriveClient
from app.services.gmail_client import GmailClient
from app.services.vault_loader import VaultLoader

router = APIRouter()


class CaseRefreshResponse(BaseModel):
    """Response payload for the case refresh endpoint."""

    total_documents: int
    gmail_messages: int
    drive_files: int
    vault_documents: int
    agent_summaries: List[dict] = Field(
        ..., description="Outputs from specialized analysis agents."
    )


class CaseAssistantRequest(BaseModel):
    """Request payload for generating a guided draft response."""

    prompt: str = Field(..., description="What to draft or answer.")
    top_k: int = Field(6, ge=1, le=25, description="Max documents used for drafting context.")


class CaseAssistantResponse(BaseModel):
    """Response payload with specialist outputs and final drafted text."""

    categorized_counts: dict[str, int]
    documents_used: int
    agent_summaries: List[dict]
    draft: str


@router.get("/health")
def healthcheck() -> dict:
    """Basic health endpoint."""

    return {"status": "ok"}


def _build_documents_from_gmail(messages: List[dict]) -> List[Document]:
    documents: List[Document] = []
    for message in messages:
        snippet = message.get("snippet", "")
        payload = message.get("payload", {})
        headers = {h.get("name", "").lower(): h.get("value", "") for h in payload.get("headers", [])}
        body_text = _extract_gmail_body_text(payload)
        doc_id = message.get("id", str(uuid4()))
        subject = headers.get("subject", "(no subject)")
        sender = headers.get("from", "unknown sender")
        documents.append(
            Document(
                page_content=f"Email subject: {subject}\nFrom: {sender}\nSnippet: {snippet}\nBody:\n{body_text}".strip(),
                metadata={"id": doc_id, "source": "gmail", "category": _categorize_text(f"{subject} {snippet} {body_text}")},
            )
        )
    return documents


def _build_documents_from_drive(files: List[dict]) -> List[Document]:
    documents: List[Document] = []
    for file in files:
        doc_id = file.get("id", str(uuid4()))
        description = f"Drive file: {file.get('name')} ({file.get('mimeType')})"
        documents.append(
            Document(page_content=description, metadata={"id": doc_id, "source": "drive"})
        )
    return documents


def _build_documents_from_vault(paths: List[str]) -> List[Document]:
    documents: List[Document] = []
    for path in paths:
        documents.append(
            Document(
                page_content=f"Vault file: {path}",
                metadata={
                    "id": str(uuid4()),
                    "source": "vault",
                    "path": path,
                    "category": _categorize_text(path),
                },
            )
        )
    return documents


def _extract_gmail_body_text(payload: dict) -> str:
    data = payload.get("body", {}).get("data")
    if data:
        return _decode_b64(data)
    for part in payload.get("parts", []):
        mime_type = part.get("mimeType", "")
        part_data = part.get("body", {}).get("data")
        if part_data and mime_type in {"text/plain", "text/html"}:
            return _strip_html(_decode_b64(part_data)) if mime_type == "text/html" else _decode_b64(part_data)
    return ""


def _decode_b64(value: str) -> str:
    try:
        return base64.urlsafe_b64decode(value.encode("utf-8")).decode("utf-8", errors="ignore")
    except Exception:
        return ""


def _strip_html(raw_text: str) -> str:
    return re.sub(r"<[^>]+>", " ", raw_text)


def _categorize_text(text: str) -> str:
    lowered = text.lower()
    rules = {
        "medical": ["doctor", "clinic", "medical", "diagnosis", "treatment"],
        "decision": ["decision", "adjudicator", "ruling", "denied", "approved"],
        "appeal": ["appeal", "reconsideration", "tribunal", "review"],
        "finance": ["benefit", "payment", "wage", "invoice", "expense"],
        "deadline": ["deadline", "by ", "due", "within", "days"],
    }
    for category, keywords in rules.items():
        if any(keyword in lowered for keyword in keywords):
            return category
    return "general"


def _category_counts(documents: List[Document]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for document in documents:
        category = str(document.metadata.get("category", "general"))
        counts[category] = counts.get(category, 0) + 1
    return counts


@router.post("/cases/refresh", response_model=CaseRefreshResponse)
def refresh_case(  # pragma: no cover - integration focused
    settings: Settings = Depends(get_settings),
) -> CaseRefreshResponse:
    """Ingest the latest data from Gmail, Drive, and the local case vault."""

    gmail_client = GmailClient(
        client_id=settings.google_client_id,
        client_secret=settings.google_client_secret,
        refresh_token=settings.google_refresh_token,
    )
    drive_client = DriveClient(
        client_id=settings.google_client_id,
        client_secret=settings.google_client_secret,
        refresh_token=settings.google_refresh_token,
    )
    vault_loader = VaultLoader(settings.case_vault_path)

    gmail_messages = gmail_client.fetch_recent_messages(query="subject:WCB OR WCB", max_results=50)
    drive_files = drive_client.list_case_files(folder_id="root")
    vault_paths = [str(path) for path in vault_loader.discover_files()]

    documents = [
        *_build_documents_from_gmail(gmail_messages),
        *_build_documents_from_drive(drive_files),
        *_build_documents_from_vault(vault_paths),
    ]

    vector_store = build_index(documents)

    agents = [
        LoopholeFinder(),
        FairnessReviewExpert(),
        AppealStrategist(),
        DirtyTacticsDefender(),
        CaseMemoryVault(),
    ]

    agent_results = [agent.run(documents) for agent in agents]
    total_documents = len(documents)
    return CaseRefreshResponse(
        total_documents=total_documents,
        gmail_messages=len(gmail_messages),
        drive_files=len(drive_files),
        vault_documents=len(vault_paths),
        agent_summaries=[result.__dict__ for result in agent_results],
    )


@router.post("/cases/assist", response_model=CaseAssistantResponse)
def assist_with_case(
    request: CaseAssistantRequest,
    settings: Settings = Depends(get_settings),
) -> CaseAssistantResponse:
    """Generate a case draft from current Gmail/Drive/vault evidence and specialist analysis."""

    gmail_client = GmailClient(
        client_id=settings.google_client_id,
        client_secret=settings.google_client_secret,
        refresh_token=settings.google_refresh_token,
    )
    drive_client = DriveClient(
        client_id=settings.google_client_id,
        client_secret=settings.google_client_secret,
        refresh_token=settings.google_refresh_token,
    )
    vault_loader = VaultLoader(settings.case_vault_path)

    gmail_messages = gmail_client.fetch_recent_messages(query="subject:WCB OR WCB", max_results=50)
    drive_files = drive_client.list_case_files(folder_id="root")
    vault_paths = [str(path) for path in vault_loader.discover_files()]
    documents = [
        *_build_documents_from_gmail(gmail_messages),
        *_build_documents_from_drive(drive_files),
        *_build_documents_from_vault(vault_paths),
    ]

    vector_store = build_index(documents)
    focused_context = vector_store.similarity_search(request.prompt, k=request.top_k)

    agents = [
        LoopholeFinder(),
        FairnessReviewExpert(),
        AppealStrategist(),
        DirtyTacticsDefender(),
        CaseMemoryVault(),
    ]
    agent_results = [agent.run(focused_context) for agent in agents]
    draft = draft_case_response(
        prompt=request.prompt,
        context=focused_context,
        agent_results=agent_results,
    )

    return CaseAssistantResponse(
        categorized_counts=_category_counts(documents),
        documents_used=len(focused_context),
        agent_summaries=[result.__dict__ for result in agent_results],
        draft=draft,
    )
