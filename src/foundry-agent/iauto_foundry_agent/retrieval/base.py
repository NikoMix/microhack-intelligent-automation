"""Retrieval primitives shared by every backend.

A :class:`Retriever` turns a natural-language query into ranked :class:`SearchHit` objects.
Both the local BM25 index and the Azure AI Search client implement the same tiny protocol,
so the agent's RAG tool is backend-agnostic.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from iauto_foundry_agent.documents import Document

_TOKEN_RE = re.compile(r"[a-z0-9]+")

# A deliberately small English stop-word set. Lexical RAG benefits from dropping the most
# common, low-signal tokens without depending on a heavyweight NLP package.
_STOPWORDS: frozenset[str] = frozenset(
    {
        "a",
        "an",
        "and",
        "are",
        "as",
        "at",
        "be",
        "but",
        "by",
        "can",
        "do",
        "does",
        "for",
        "from",
        "how",
        "i",
        "if",
        "in",
        "is",
        "it",
        "its",
        "me",
        "my",
        "of",
        "on",
        "or",
        "our",
        "should",
        "so",
        "that",
        "the",
        "their",
        "them",
        "then",
        "there",
        "these",
        "they",
        "this",
        "to",
        "was",
        "we",
        "what",
        "when",
        "where",
        "which",
        "who",
        "why",
        "will",
        "with",
        "you",
        "your",
    }
)


def tokenize(text: str) -> list[str]:
    """Lowercase, split into alphanumeric tokens, and drop stop-words."""
    return [tok for tok in _TOKEN_RE.findall(text.lower()) if tok not in _STOPWORDS]


@dataclass(frozen=True, slots=True)
class SearchHit:
    """A retrieved document together with its relevance score (higher is better)."""

    document: Document
    score: float


@runtime_checkable
class Retriever(Protocol):
    """Anything that can rank knowledge-base documents for a query."""

    def search(self, query: str, *, top_k: int = 4) -> list[SearchHit]:
        """Return up to ``top_k`` documents most relevant to ``query``."""
        ...
