"""Indexing and categorization logic."""
from __future__ import annotations

import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Dict, Iterable, List

from pg_keeper.models import Category, Document, IndexedRecord


KEYWORDS = {
    Category.MEDICAL: {"clinic", "doctor", "treatment", "diagnosis", "therapy", "injury"},
    Category.EMPLOYMENT: {"employer", "shift", "duty", "salary", "position", "supervisor"},
    Category.ADMIN: {"form", "submission", "deadline", "reference", "claim number", "intake"},
    Category.LEGAL: {"appeal", "statute", "law", "precedent", "hearing", "adjudicator"},
    Category.CORRESPONDENCE: {"email", "conversation", "thread", "re", "fwd", "correspondence"},
    Category.FINANCIAL: {"payment", "invoice", "benefit", "reimbursement", "cost", "bill"},
    Category.EVIDENCE: {"photo", "witness", "evidence", "statement", "report", "investigation"},
}


@dataclass
class CaseIndexer:
    """Classifies and indexes documents using simple keyword heuristics."""

    def categorize(self, document: Document) -> Category:
        text = f"{document.title}\n{document.content}".lower()
        counts: Dict[Category, int] = defaultdict(int)
        for category, tokens in KEYWORDS.items():
            for token in tokens:
                if token in text:
                    counts[category] += 1
        if not counts:
            return Category.UNKNOWN
        top_category, _ = Counter(counts).most_common(1)[0]
        return top_category

    def extract_key_terms(self, document: Document, limit: int = 10) -> List[str]:
        text = f"{document.title} {document.content}".lower()
        candidates = re.findall(r"[a-zA-Z]{4,}", text)
        common = Counter(candidates).most_common(limit)
        return [term for term, _ in common]

    def index(self, documents: Iterable[Document]) -> List[IndexedRecord]:
        indexed: List[IndexedRecord] = []
        for document in documents:
            document.category = self.categorize(document)
            indexed.append(IndexedRecord(document=document, key_terms=self.extract_key_terms(document)))
        return indexed
