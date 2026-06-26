"""In-memory Okapi BM25 retriever — the zero-Azure local fallback index.

BM25 is the classic, strong lexical ranking function used by search engines. Implementing it
directly keeps the local lab path free of any third-party (and any *paid*) search dependency
while still giving learners realistic, relevance-ranked retrieval. Swap it for Azure AI Search
(vector + semantic ranking) by flipping ``RETRIEVER_BACKEND`` — no feature-code change.
"""

from __future__ import annotations

import math
from collections import Counter
from collections.abc import Sequence
from pathlib import Path

from iauto_foundry_agent.documents import Document, load_documents
from iauto_foundry_agent.retrieval.base import SearchHit, tokenize

_DEFAULT_K1 = 1.5
_DEFAULT_B = 0.75


class BM25LocalRetriever:
    """Rank documents with Okapi BM25 over an in-memory token index.

    Args:
        documents: corpus to index.
        k1: term-frequency saturation (typical range 1.2-2.0).
        b: length-normalisation strength (0 = none, 1 = full).
    """

    def __init__(
        self,
        documents: Sequence[Document],
        *,
        k1: float = _DEFAULT_K1,
        b: float = _DEFAULT_B,
    ) -> None:
        self._documents: tuple[Document, ...] = tuple(documents)
        self._k1 = k1
        self._b = b

        self._doc_tokens: list[Counter[str]] = [
            Counter(tokenize(doc.searchable_text)) for doc in self._documents
        ]
        self._doc_len: list[int] = [sum(tf.values()) for tf in self._doc_tokens]
        n_docs = len(self._documents)
        self._avgdl: float = (sum(self._doc_len) / n_docs) if n_docs else 0.0
        self._idf: dict[str, float] = self._compute_idf(n_docs)

    def _compute_idf(self, n_docs: int) -> dict[str, float]:
        document_frequency: Counter[str] = Counter()
        for tf in self._doc_tokens:
            document_frequency.update(tf.keys())
        # BM25+ idf variant: strictly positive, so common terms never push scores negative.
        return {
            term: math.log(1.0 + (n_docs - df + 0.5) / (df + 0.5))
            for term, df in document_frequency.items()
        }

    def _score(self, query_terms: Sequence[str], doc_index: int) -> float:
        tf = self._doc_tokens[doc_index]
        if not tf:
            return 0.0
        dl = self._doc_len[doc_index]
        length_norm = self._k1 * (1.0 - self._b + self._b * dl / self._avgdl)
        score = 0.0
        for term in query_terms:
            freq = tf.get(term, 0)
            if freq == 0:
                continue
            idf = self._idf.get(term, 0.0)
            score += idf * (freq * (self._k1 + 1.0)) / (freq + length_norm)
        return score

    def search(self, query: str, *, top_k: int = 4) -> list[SearchHit]:
        """Return up to ``top_k`` documents most relevant to ``query`` (BM25-ranked)."""
        if top_k <= 0 or not self._documents:
            return []
        query_terms = tokenize(query)
        if not query_terms:
            return []

        scored: list[tuple[float, int]] = []
        for idx in range(len(self._documents)):
            score = self._score(query_terms, idx)
            if score > 0.0:
                scored.append((score, idx))

        # Sort by score desc, breaking ties on original order for deterministic output.
        scored.sort(key=lambda pair: (-pair[0], pair[1]))
        return [
            SearchHit(document=self._documents[idx], score=score) for score, idx in scored[:top_k]
        ]

    @classmethod
    def from_path(cls, path: str | Path | None = None) -> BM25LocalRetriever:
        """Build a retriever from a JSON knowledge-base file (or the bundled sample)."""
        return cls(load_documents(path))
