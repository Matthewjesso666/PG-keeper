"""Case agent pipeline."""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Iterable, List, Optional

from pg_keeper.analysis.specialists import (
    AppealStrategist,
    CaseMemoryVault,
    DirtyTacticsDefender,
    FairnessReviewExpert,
    LoopholeFinder,
    Specialist,
)
from pg_keeper.config import AgentConfig, CaseVaultConfig, GoogleAuthConfig
from pg_keeper.data_sources.case_vault import CaseVaultReader
from pg_keeper.data_sources.drive_client import DriveClient
from pg_keeper.data_sources.gmail_client import GmailClient
from pg_keeper.indexer import CaseIndexer
from pg_keeper.llm import EchoLLMClient, LLMClient
from pg_keeper.models import Document, DraftedResponse, IndexedRecord, SpecialistFinding

logger = logging.getLogger(__name__)


@dataclass
class CaseAgent:
    """Coordinates data ingestion, analysis, and drafting."""

    config: AgentConfig
    llm_client: LLMClient = field(default_factory=EchoLLMClient)
    google_auth: Optional[GoogleAuthConfig] = None
    case_vault: Optional[CaseVaultConfig] = None

    def __post_init__(self) -> None:
        self.indexer = CaseIndexer()
        self.specialists: List[Specialist] = [
            LoopholeFinder(self.llm_client),
            FairnessReviewExpert(self.llm_client),
            AppealStrategist(self.llm_client),
            DirtyTacticsDefender(self.llm_client),
            CaseMemoryVault(self.llm_client),
        ]
        self.gmail_client = GmailClient(self.google_auth) if self.google_auth else None
        self.drive_client = DriveClient(self.google_auth) if self.google_auth else None
        self.vault_reader = CaseVaultReader(self.case_vault) if self.case_vault else None

    def collect_documents(self) -> List[Document]:
        documents: List[Document] = []
        if self.vault_reader:
            documents.extend(self.vault_reader.load_documents())
            logger.info("Loaded %s vault documents", len(documents))
        if self.gmail_client:
            try:
                docs = self.gmail_client.fetch_recent_messages()
                documents.extend(docs)
                logger.info("Fetched %s Gmail messages", len(docs))
            except ImportError as exc:  # pragma: no cover - import side effect
                logger.warning("Skipping Gmail sync: %s", exc)
        if self.drive_client:
            try:
                docs = self.drive_client.fetch_recent_files()
                documents.extend(docs)
                logger.info("Fetched %s Drive files", len(docs))
            except ImportError as exc:  # pragma: no cover - import side effect
                logger.warning("Skipping Drive sync: %s", exc)
        return documents

    def index_documents(self, documents: Iterable[Document]) -> List[IndexedRecord]:
        indexed = self.indexer.index(documents)
        logger.info("Indexed %s documents", len(indexed))
        return indexed

    def run_specialists(self, documents: Iterable[Document]) -> List[SpecialistFinding]:
        findings: List[SpecialistFinding] = []
        for specialist in self.specialists:
            findings.append(specialist.analyze(documents))
        return findings

    def draft_response(self, findings: Iterable[SpecialistFinding]) -> DraftedResponse:
        bullets = []
        for finding in findings:
            bullets.append(f"- {finding.specialist}: {finding.recommended_actions[:2] or finding.summary[:120]}")
        body_lines = [
            f"Dear {self.config.response_recipient},",
            "",
            "Here is the latest assessment for the WCB case:",
            *bullets,
            "",
            "Let me know if you want me to file or escalate any of the above.",
        ]
        return DraftedResponse(subject="Case update and next actions", body="\n".join(body_lines))

    def run(self) -> DraftedResponse:
        documents = self.collect_documents()
        indexed = self.index_documents(documents)
        findings = self.run_specialists([record.document for record in indexed])
        draft = self.draft_response(findings)
        if self.config.dry_run:
            logger.info("Dry run: Response drafted but not sent")
        return draft
