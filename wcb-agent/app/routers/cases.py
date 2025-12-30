"""API routes for managing WCB case data and analysis."""
from __future__ import annotations

from typing import List
from uuid import uuid4

from fastapi import APIRouter, Depends
from langchain.schema import Document
from pydantic import BaseModel, Field

from app.agents.analysis import (
    AppealStrategist,
    CaseMemoryVault,
    DirtyTacticsDefender,
    FairnessReviewExpert,
    LoopholeFinder,
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


@router.get("/health")
def healthcheck() -> dict:
    """Basic health endpoint."""

    return {"status": "ok"}


def _build_documents_from_gmail(messages: List[dict]) -> List[Document]:
    documents: List[Document] = []
    for message in messages:
        snippet = message.get("snippet", "")
        doc_id = message.get("id", str(uuid4()))
        documents.append(
            Document(
                page_content=snippet,
                metadata={"id": doc_id, "source": "gmail"},
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
                metadata={"id": str(uuid4()), "source": "vault", "path": path},
            )
        )
    return documents


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
