"""Azure AI Search retrieval and citation formatting."""

from __future__ import annotations

import inspect
from collections.abc import AsyncIterable, Awaitable, Mapping
from dataclasses import dataclass
from typing import Protocol, cast

from azure.identity.aio import DefaultAzureCredential
from azure.search.documents.aio import SearchClient

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
