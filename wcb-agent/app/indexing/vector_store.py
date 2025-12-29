"""Vector store utilities for organizing case documents."""
from __future__ import annotations

from typing import List, Sequence

from langchain.embeddings import OpenAIEmbeddings
from langchain.schema import Document
from langchain.vectorstores import FAISS


def build_index(documents: Sequence[Document]) -> FAISS:
    """Create a FAISS vector index from LangChain documents."""

    embeddings = OpenAIEmbeddings()
    return FAISS.from_documents(list(documents), embedding=embeddings)


def similarity_search(store: FAISS, query: str, k: int = 5) -> List[Document]:
    """Run a similarity search over the vector store."""

    return store.similarity_search(query, k=k)
