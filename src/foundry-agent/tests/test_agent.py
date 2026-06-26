from __future__ import annotations

from typing import Any

from iauto_foundry_agent.agent import FoundryRagAgent
from iauto_foundry_agent.retrieval import AzureSearchRetriever, Retriever
from iauto_foundry_agent.settings import Settings
from iauto_foundry_agent.summarizer import ContextSummarizer
from iauto_inference import ChatResult

from tests.test_retrieval import FakeSearchClient


class FakeAgent:
    def __init__(self) -> None:
        self.prompt = ""

    async def run(self, messages: str, **kwargs: Any) -> object:
        self.prompt = messages
        _ = kwargs
        return type("Response", (), {"text": "Submit within 30 days [1]."})()


class FakeInferenceClient:
    async def acomplete(
        self,
        messages: object,
        *,
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        **extra: Any,
    ) -> ChatResult:
        _ = messages, model, temperature, max_tokens, extra
        return ChatResult(
            text="Claims must be submitted within 30 days [1].", model="m", provider="p"
        )


async def test_agent_builds_grounded_prompt_and_returns_citations() -> None:
    search = FakeSearchClient(
        [
            {
                "title": "Contoso Expense Policy",
                "section": "Submission Timing",
                "content": "Claims must be submitted within 30 calendar days.",
                "source_path": "knowledge/expense-policy.md",
                "chunk_id": "abc123",
            }
        ]
    )
    fake_agent = FakeAgent()

    def factory(_: Retriever) -> FakeAgent:
        return fake_agent

    runner = FoundryRagAgent(
        Settings(search_endpoint="https://search.example", agent_runtime="modular"),
        AzureSearchRetriever(search, top_k=4),
        ContextSummarizer(FakeInferenceClient()),
        agent_factory=factory,
    )

    result = await runner.answer("When do I submit expenses?")

    assert result.answer == "Submit within 30 days [1]."
    assert "Retrieved knowledge-base context" in fake_agent.prompt
    assert "Claims must be submitted within 30 calendar days." in fake_agent.prompt
    assert result.retrieval.citations == ("[1] Contoso Expense Policy — Submission Timing",)
