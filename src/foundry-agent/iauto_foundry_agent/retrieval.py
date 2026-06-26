"""Knowledge-base retrieval (offline BM25 + Azure AI Search) and citation formatting."""

from __future__ import annotations

import inspect
import math
import re
from collections import Counter
from collections.abc import AsyncIterable, Awaitable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, cast

from azure.identity.aio import DefaultAzureCredential
from azure.search.documents.aio import SearchClient

from iauto_foundry_agent.ingestion import KnowledgeChunk, load_sample_chunks
from iauto_foundry_agent.settings import Settings
from iauto_foundry_agent.telemetry import start_span


class SearchClientProtocol(Protocol):
    """Narrow async subset of Azure Search used by the retriever."""

    def search(
        self,
        search_text: str,
        *,
        top: int,
        select: list[str],
    ) -> AsyncIterable[Mapping[str, object]] | Awaitable[AsyncIterable[Mapping[str, object]]]:
        """Return async search results."""
        ...


@dataclass(frozen=True, slots=True)
class RetrievedChunk:
    """One grounded knowledge chunk returned from Azure AI Search."""

    title: str
    section: str
    content: str
    source_path: str
    chunk_id: str
    score: float | None = None

    @property
    def citation_label(self) -> str:
        return f"{self.title} — {self.section}"


@dataclass(frozen=True, slots=True)
class RetrievalResult:
    """Formatted retrieval output for prompts and CLI display."""

    query: str
    chunks: tuple[RetrievedChunk, ...]

    @property
    def citations(self) -> tuple[str, ...]:
        return tuple(
            f"[{index}] {chunk.citation_label}" for index, chunk in enumerate(self.chunks, 1)
        )

    def format_context(self) -> str:
        if not self.chunks:
            return "No relevant knowledge-base passages were found."
        blocks = []
        for index, chunk in enumerate(self.chunks, 1):
            blocks.append(
                f"[{index}] {chunk.citation_label}\n"
                f"Source: {chunk.source_path}#{chunk.chunk_id}\n"
                f"{chunk.content}"
            )
        return "\n\n".join(blocks)

    def format_citations(self) -> str:
        return "\n".join(self.citations) if self.citations else "No citations."


class Retriever(Protocol):
    """Async retrieval surface implemented by the offline and Azure backends."""

    async def retrieve(self, query: str) -> RetrievalResult:
        """Return grounded knowledge chunks for the query."""
        ...


class AzureSearchRetriever:
    """Async Azure AI Search retriever with a mockable client protocol."""

    def __init__(self, client: SearchClientProtocol, *, top_k: int) -> None:
        self._client = client
        self._top_k = top_k

    async def retrieve(self, query: str) -> RetrievalResult:
        """Search the index and return normalized chunks."""
        with start_span("search.retrieve") as span:
            span.set_attribute("search.query_length", len(query))
            results = self._client.search(
                query,
                top=self._top_k,
                select=["title", "section", "content", "source_path", "chunk_id"],
            )
            if inspect.isawaitable(results):
                results = await results
            chunks = [self._to_chunk(item) async for item in results]
            span.set_attribute("search.result_count", len(chunks))
        return RetrievalResult(query=query, chunks=tuple(chunks))

    @staticmethod
    def _to_chunk(item: Mapping[str, object]) -> RetrievedChunk:
        score = item.get("@search.score")
        return RetrievedChunk(
            title=str(item.get("title", "Untitled")),
            section=str(item.get("section", "Overview")),
            content=str(item.get("content", "")),
            source_path=str(item.get("source_path", "knowledge")),
            chunk_id=str(item.get("chunk_id", "chunk")),
            score=float(score) if isinstance(score, int | float) else None,
        )


_TOKEN_RE = re.compile(r"[a-z0-9]+")
_MIN_TOKEN_LENGTH = 2
_BM25_K1 = 1.5
_BM25_B = 0.75
_STOPWORDS = frozenset(
    {
        "the",
        "a",
        "an",
        "and",
        "or",
        "of",
        "to",
        "in",
        "on",
        "for",
        "is",
        "are",
        "be",
        "do",
        "how",
        "what",
        "when",
        "where",
        "which",
        "with",
        "my",
    }
)


def _tokenize(text: str) -> list[str]:
    return [
        token
        for token in _TOKEN_RE.findall(text.lower())
        if len(token) >= _MIN_TOKEN_LENGTH and token not in _STOPWORDS
    ]


def _document_text(chunk: KnowledgeChunk) -> str:
    return f"{chunk.title}\n{chunk.section}\n{chunk.content}"


@dataclass(frozen=True, slots=True)
class _IndexedDoc:
    """A knowledge chunk with precomputed BM25 term statistics."""

    chunk: KnowledgeChunk
    term_freq: Mapping[str, int]
    length: int


class KeywordRetriever:
    """License-free offline BM25 retriever over the in-memory knowledge base.

    Needs no Azure resources, so Lab 4 runs fully offline with GitHub Models before any
    Azure AI Search upgrade. Ranks the committed markdown knowledge base with Okapi BM25.
    """

    def __init__(self, chunks: Sequence[KnowledgeChunk], *, top_k: int) -> None:
        self._top_k = top_k
        docs: list[_IndexedDoc] = []
        document_freq: Counter[str] = Counter()
        for chunk in chunks:
            term_freq: Counter[str] = Counter(_tokenize(_document_text(chunk)))
            docs.append(
                _IndexedDoc(chunk=chunk, term_freq=term_freq, length=sum(term_freq.values()))
            )
            document_freq.update(term_freq.keys())
        self._docs = docs
        doc_count = len(docs)
        self._avg_length = sum(doc.length for doc in docs) / doc_count if doc_count else 0.0
        self._idf = {
            term: math.log(1.0 + (doc_count - freq + 0.5) / (freq + 0.5))
            for term, freq in document_freq.items()
        }

    @classmethod
    def from_sample_knowledge(cls, *, top_k: int, data_dir: Path | None = None) -> KeywordRetriever:
        """Build a retriever from the committed markdown knowledge base."""
        return cls(load_sample_chunks(data_dir), top_k=top_k)

    async def retrieve(self, query: str) -> RetrievalResult:
        """Rank knowledge chunks for the query with offline BM25 scoring."""
        with start_span("retrieval.offline") as span:
            span.set_attribute("retrieval.query_length", len(query))
            scored = self._rank(_tokenize(query))
            chunks = tuple(self._to_chunk(doc, score) for doc, score in scored)
            span.set_attribute("retrieval.result_count", len(chunks))
        return RetrievalResult(query=query, chunks=chunks)

    def _rank(self, query_terms: Sequence[str]) -> list[tuple[_IndexedDoc, float]]:
        if not query_terms or not self._docs:
            return []
        unique_terms = set(query_terms)
        scored: list[tuple[_IndexedDoc, float]] = []
        for doc in self._docs:
            score = self._score(doc, unique_terms)
            if score > 0.0:
                scored.append((doc, score))
        scored.sort(key=lambda item: item[1], reverse=True)
        return scored[: max(self._top_k, 0)]

    def _score(self, doc: _IndexedDoc, query_terms: set[str]) -> float:
        if self._avg_length == 0.0:
            return 0.0
        score = 0.0
        for term in query_terms:
            term_freq = doc.term_freq.get(term, 0)
            if term_freq == 0:
                continue
            denominator = term_freq + _BM25_K1 * (
                1.0 - _BM25_B + _BM25_B * doc.length / self._avg_length
            )
            score += self._idf.get(term, 0.0) * (term_freq * (_BM25_K1 + 1.0)) / denominator
        return score

    @staticmethod
    def _to_chunk(doc: _IndexedDoc, score: float) -> RetrievedChunk:
        chunk = doc.chunk
        return RetrievedChunk(
            title=chunk.title,
            section=chunk.section,
            content=chunk.content,
            source_path=chunk.source_path,
            chunk_id=chunk.chunk_id,
            score=score,
        )


class SearchClientFactory:
    """Owns Azure Search credential/client lifetime for CLI commands."""

    def __init__(self, settings: Settings) -> None:
        settings.require_search()
        self._settings = settings
        self._credential = DefaultAzureCredential()
        self._client = SearchClient(
            endpoint=settings.search_endpoint,
            index_name=settings.search_index,
            credential=self._credential,
        )

    def retriever(self) -> AzureSearchRetriever:
        return AzureSearchRetriever(
            cast(SearchClientProtocol, self._client),
            top_k=self._settings.search_top_k,
        )

    async def close(self) -> None:
        await self._client.close()
        await self._credential.close()
