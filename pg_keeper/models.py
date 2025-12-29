"""Shared domain models."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional


class SourceType(str, Enum):
    GMAIL = "gmail"
    DRIVE = "drive"
    CASE_VAULT = "case_vault"
    MANUAL = "manual"


class Category(str, Enum):
    MEDICAL = "medical"
    EMPLOYMENT = "employment"
    ADMIN = "administrative"
    LEGAL = "legal"
    CORRESPONDENCE = "correspondence"
    FINANCIAL = "financial"
    EVIDENCE = "evidence"
    UNKNOWN = "uncategorized"


@dataclass
class Document:
    identifier: str
    title: str
    source: SourceType
    content: str
    created_at: Optional[datetime] = None
    path: Optional[Path] = None
    metadata: Dict[str, str] = field(default_factory=dict)
    category: Category = Category.UNKNOWN


@dataclass
class IndexedRecord:
    document: Document
    key_terms: List[str]


@dataclass
class SpecialistFinding:
    specialist: str
    summary: str
    risks: List[str] = field(default_factory=list)
    opportunities: List[str] = field(default_factory=list)
    recommended_actions: List[str] = field(default_factory=list)


@dataclass
class DraftedResponse:
    subject: str
    body: str
    attachments: List[Path] = field(default_factory=list)
