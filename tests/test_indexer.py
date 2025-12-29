from pg_keeper.indexer import CaseIndexer, Category
from pg_keeper.models import Document, SourceType


def make_doc(title: str, content: str) -> Document:
    return Document(identifier="1", title=title, source=SourceType.MANUAL, content=content)


def test_categorize_medical():
    doc = make_doc("Medical report", "Doctor confirmed injury and therapy plan")
    category = CaseIndexer().categorize(doc)
    assert category == Category.MEDICAL


def test_extract_key_terms_limits_size():
    doc = make_doc("Payment notice", "payment payment bill bill bill")
    terms = CaseIndexer().extract_key_terms(doc, limit=2)
    assert terms == ["payment", "bill"]


def test_index_applies_categories_and_key_terms():
    doc = make_doc("Appeal document", "The appeal hearing and precedent discussion")
    indexed = CaseIndexer().index([doc])
    assert indexed[0].document.category == Category.LEGAL
    assert "appeal" in indexed[0].key_terms
