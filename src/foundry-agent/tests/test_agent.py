"""Tests for the agent wiring and an offline end-to-end function-calling run.

The end-to-end test drives the *real* Microsoft Agent Framework loop using a stubbed
``AsyncOpenAI`` that replays genuine ``openai`` completion objects — proving the RAG tool is
actually invoked and the answer is grounded, with no network and no provider.
"""

from __future__ import annotations

import json
from types import SimpleNamespace

import pytest
from agent_framework.openai import OpenAIChatCompletionClient
from iauto_foundry_agent.agent import (
    GroundedKnowledgeAgent,
    answer,
    build_agent,
    build_chat_client,
    format_context,
    make_search_tool,
)
from iauto_foundry_agent.errors import FoundryAgentError
from iauto_foundry_agent.retrieval.local import BM25LocalRetriever
from openai import AsyncOpenAI

from ._openai_factories import make_stub_client, text_completion, tool_call_completion


class _FakeInference:
    def __init__(self, raw_async_client: AsyncOpenAI) -> None:
        self.raw_async_client = raw_async_client


def _fake_settings(model: str, provider: str = "github") -> SimpleNamespace:
    return SimpleNamespace(default_model=lambda: model, provider=SimpleNamespace(value=provider))


def test_build_chat_client_borrows_transport_and_model() -> None:
    raw = AsyncOpenAI(api_key="dummy", base_url="http://localhost:9999/v1")
    client = build_chat_client(_FakeInference(raw), _fake_settings("gpt-4o-mini"))  # type: ignore[arg-type]
    assert isinstance(client, OpenAIChatCompletionClient)
    model_attr = getattr(client, "model_id", None) or getattr(client, "model", None)
    assert model_attr == "gpt-4o-mini"
    assert client.client is raw


def test_build_chat_client_requires_a_model() -> None:
    raw = AsyncOpenAI(api_key="dummy", base_url="http://localhost:9999/v1")
    with pytest.raises(FoundryAgentError, match="No model/deployment configured"):
        build_chat_client(_FakeInference(raw), _fake_settings(""))  # type: ignore[arg-type]


def test_format_context_numbers_and_cites(local_retriever: BM25LocalRetriever) -> None:
    hits = local_retriever.search("vpn globalprotect", top_k=1)
    rendered = format_context(hits)
    assert rendered.startswith("[1]")
    assert "source:" in rendered
    assert "GlobalProtect" in rendered


def test_format_context_handles_no_hits() -> None:
    assert format_context([]) == "No matching knowledge-base passages were found."


def test_search_tool_returns_grounded_context(local_retriever: BM25LocalRetriever) -> None:
    tool = make_search_tool(local_retriever, top_k=1)
    assert tool.__name__ == "search_knowledge_base"
    out = tool("how do I connect to the vpn")
    assert "[1]" in out
    assert "[2]" not in out  # top_k=1 binding respected
    assert "GlobalProtect" in out


def test_build_agent_uses_injected_collaborators(
    local_retriever: BM25LocalRetriever,
) -> None:
    stub = make_stub_client([])
    chat_client = OpenAIChatCompletionClient(async_client=stub.client, model="test-model")
    agent = build_agent(chat_client=chat_client, retriever=local_retriever, name="kb-bot")
    assert agent.name == "kb-bot"


async def test_grounded_agent_search_delegates_to_retriever(
    local_retriever: BM25LocalRetriever,
) -> None:
    stub = make_stub_client([])
    chat_client = OpenAIChatCompletionClient(async_client=stub.client, model="test-model")
    agent = build_agent(chat_client=chat_client, retriever=local_retriever)
    grounded = GroundedKnowledgeAgent(agent, retriever=local_retriever, top_k=2)
    hits = grounded.search("password reset", top_k=1)
    assert [h.document.id for h in hits] == ["d2"]


async def test_end_to_end_function_calling_is_grounded(
    local_retriever: BM25LocalRetriever,
) -> None:
    stub = make_stub_client(
        [
            tool_call_completion("search_knowledge_base", json.dumps({"query": "vpn"})),
            text_completion("Use GlobalProtect to connect to the VPN. [1]"),
        ]
    )
    chat_client = OpenAIChatCompletionClient(async_client=stub.client, model="test-model")
    grounded = GroundedKnowledgeAgent.from_env(chat_client=chat_client, retriever=local_retriever)

    reply = await grounded.ask("How do I connect to the VPN?")

    assert "GlobalProtect" in reply
    # Two model round-trips: the tool-call request, then the grounded answer.
    assert len(stub.calls) == 2
    # The first request advertised the RAG tool to the model.
    assert "tools" in stub.calls[0]
    # The second request carried the retrieved passage back to the model (tool executed).
    assert "GlobalProtect" in json.dumps(stub.calls[1].get("messages", []))


async def test_answer_convenience_runs_end_to_end(
    local_retriever: BM25LocalRetriever,
) -> None:
    stub = make_stub_client(
        [
            tool_call_completion("search_knowledge_base", json.dumps({"query": "expenses"})),
            text_completion("Submit expenses in Concur. [1]"),
        ]
    )
    chat_client = OpenAIChatCompletionClient(async_client=stub.client, model="test-model")
    reply = await answer(
        "How do I submit expenses?", chat_client=chat_client, retriever=local_retriever
    )
    assert "Concur" in reply
