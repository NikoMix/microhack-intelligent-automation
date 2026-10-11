from __future__ import annotations

from collections.abc import AsyncIterator, Mapping

from iauto_foundry_agent.ingestion import KnowledgeChunk, parse_markdown
from iauto_foundry_agent.retrieval import AzureSearchRetriever, KeywordRetriever


class FakeSearchClient:
    def __init__(self, items: list[Mapping[str, object]]) -> None:
        self.items = items
        self.queries: list[str] = []

    def search(
        self,
        search_text: str,
        *,
        top: int,
        select: list[str],
    ) -> AsyncIterator[Mapping[str, object]]:
        self.queries.append(search_text)
        _ = top, select
        return self._iter_items()

    async def _iter_items(self) -> AsyncIterator[Mapping[str, object]]:
        for item in self.items:
            yield item


async def test_retrieval_formats_citations() -> None:
    client = FakeSearchClient(
        [
            {
                "title": "Contoso Expense Policy",
                "section": "Approval Thresholds",
                "content": "Expenses up to 250 EUR require manager approval.",
                "source_path": "knowledge/expense-policy.md",
                "chunk_id": "abc123",
                "@search.score": 2.5,
            }
        ]
    )

    result = await AzureSearchRetriever(client, top_k=3).retrieve("expense approvals")

    assert client.queries == ["expense approvals"]
    assert result.citations == ("[1] Contoso Expense Policy — Approval Thresholds",)
    assert "Source: knowledge/expense-policy.md#abc123" in result.format_context()
    assert "Expenses up to 250 EUR" in result.format_context()


def test_parse_markdown_builds_section_chunks() -> None:
    chunks = parse_markdown(
        "sample.md",
        "# Sample Title\n\n## First Section\nOne fact.\n\n## Second Section\nTwo facts.",
    )

    assert [chunk.section for chunk in chunks] == ["First Section", "Second Section"]
    assert chunks[0].title == "Sample Title"
    assert chunks[0].source_path == "knowledge/sample.md"


def _kb_chunk(title: str, section: str, content: str, chunk_id: str) -> KnowledgeChunk:
    return KnowledgeChunk(
        id=chunk_id,
        title=title,
        section=section,
        content=content,
        source_path=f"knowledge/{chunk_id}.md",
        chunk_id=chunk_id,
    )


async def test_keyword_retriever_ranks_relevant_chunk_first() -> None:
    chunks = [
        _kb_chunk(
            "Expense Policy",
            "Approval Thresholds",
            "Expenses up to 250 EUR require manager approval.",
            "expense",
        ),
        _kb_chunk("VPN Setup", "Installation", "Install the VPN client and sign in.", "vpn"),
    ]

    result = await KeywordRetriever(chunks, top_k=2).retrieve(
        "What is the approval limit for expenses?"
    )

    assert result.chunks
    assert result.chunks[0].title == "Expense Policy"
    assert result.citations[0] == "[1] Expense Policy — Approval Thresholds"


async def test_keyword_retriever_returns_empty_for_unknown_terms() -> None:
    retriever = KeywordRetriever([_kb_chunk("VPN", "Setup", "Install the client.", "vpn")], top_k=3)

    result = await retriever.retrieve("zzz nonexistent")

    assert result.chunks == ()
    assert result.format_context() == "No relevant knowledge-base passages were found."


async def test_keyword_retriever_respects_top_k() -> None:
    chunks = [
        _kb_chunk("Doc A", "Policy", "approval approval policy", "a"),
        _kb_chunk("Doc B", "Policy", "approval policy", "b"),
        _kb_chunk("Doc C", "Policy", "approval", "c"),
    ]

    result = await KeywordRetriever(chunks, top_k=2).retrieve("approval policy")

    assert len(result.chunks) == 2


async def test_keyword_retriever_from_sample_knowledge_smoke() -> None:
    result = await KeywordRetriever.from_sample_knowledge(top_k=3).retrieve("expense approval")

    assert result.chunks
    assert all(chunk.content for chunk in result.chunks)
