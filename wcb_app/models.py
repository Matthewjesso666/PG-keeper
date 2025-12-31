"""Pydantic models for WCB Super Advocate."""

from datetime import datetime
from typing import List, Optional
from uuid import uuid4

from pydantic import BaseModel, Field


def new_id() -> str:
    """Return a new identifier string."""
    return uuid4().hex


class Document(BaseModel):
    """Represents an imported document."""

    id: str = Field(default_factory=new_id)
    filename: str
    doc_type: str = "other"
    imported_at: datetime = Field(default_factory=datetime.utcnow)
    original_path: str
    stored_path: str
    extracted_text_path: Optional[str] = None
    notes: Optional[str] = None
    status: str = "imported"


class ExtractionResult(BaseModel):
    """Captures extraction status for a document."""

    doc_id: str
    success: bool
    text_path: Optional[str] = None
    error_message: Optional[str] = None


class TimelineEntry(BaseModel):
    """Chronological entry for the case timeline."""

    event_date: str
    description: str
    source_document_id: Optional[str] = None


class Issue(BaseModel):
    """Represents an issue or concern for the case."""

    title: str
    detail: str
    related_document_id: Optional[str] = None


class DraftRecord(BaseModel):
    """Tracks generated draft artifacts."""

    draft_type: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    txt_path: str
    docx_path: str


class CaseState(BaseModel):
    """Overall state for a WCB case."""

    case_name: str
    base_path: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    factual_only: bool = True
    documents: List[Document] = Field(default_factory=list)
    timeline: List[TimelineEntry] = Field(default_factory=list)
    issues: List[Issue] = Field(default_factory=list)
    drafts: List[DraftRecord] = Field(default_factory=list)

