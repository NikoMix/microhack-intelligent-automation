from __future__ import annotations

from typing import Any

from iauto_foundry_agent.retrieval import RetrievalResult, RetrievedChunk
from iauto_foundry_agent.summarizer import ContextSummarizer
from iauto_inference import ChatResult


class FakeInferenceClient:
    def __init__(self) -> None:
        self.messages: object | None = None

    async def acomplete(
        self,
        messages: object,
        *,
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        **extra: Any,
    ) -> ChatResult:
        self.messages = messages
        _ = model, temperature, max_tokens, extra
        return ChatResult(text="Manager approval is needed up to 250 EUR [1].", model="m", provider="p")


async def test_summarizer_uses_inference_contract() -> None:
    retrieval = RetrievalResult(
        query="approval",
        chunks=(
            RetrievedChunk(
                title="Contoso Expense Policy",
                section="Approval Thresholds",
                content="Expenses up to 250 EUR require manager approval.",
                source_path="knowledge/expense-policy.md",
                chunk_id="abc123",
            ),
        ),
    )
    client = FakeInferenceClient()

    summary = await ContextSummarizer(client).summarize("Who approves?", retrieval)

    assert summary == "Manager approval is needed up to 250 EUR [1]."
    assert client.messages is not None


async def test_summarizer_short_circuits_empty_retrieval() -> None:
    client = FakeInferenceClient()
    retrieval = RetrievalResult(query="unknown", chunks=())

    summary = await ContextSummarizer(client).summarize("Unknown?", retrieval)

    assert summary == "No relevant knowledge-base passages were found."
    assert client.messages is None
