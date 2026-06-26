from __future__ import annotations

from collections.abc import AsyncIterator, Mapping

from iauto_foundry_agent.ingestion import parse_markdown
from iauto_foundry_agent.retrieval import AzureSearchRetriever


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
