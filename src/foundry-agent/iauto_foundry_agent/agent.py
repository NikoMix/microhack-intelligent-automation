"""The Foundry knowledge agent: Microsoft Agent Framework + RAG on modular inference.

This is the Copilot Studio migration target. A Copilot Studio bot couples a system prompt,
a knowledge source, and tool/topic triggers. Here the same shape is expressed in code:

* **Brain** — an Agent Framework :class:`~agent_framework.Agent` whose chat client is built
  from the shared :mod:`iauto_inference` layer, so it runs on GitHub Models (free default),
  Azure OpenAI, or Azure AI Foundry by configuration alone.
* **Knowledge** — a RAG ``search_knowledge_base`` *function tool* backed by a pluggable
  :class:`~iauto_foundry_agent.retrieval.base.Retriever` (local BM25 or Azure AI Search).
* **Grounding** — system instructions that require the model to call the tool and cite
  sources, demonstrating tool / function-calling.

We deliberately use ``OpenAIChatCompletionClient`` (the Chat Completions connector) rather
than the Responses-API client, because the free GitHub Models endpoint speaks Chat
Completions — keeping all three providers on one code path.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Annotated

from agent_framework import Agent
from agent_framework.openai import OpenAIChatCompletionClient
from iauto_inference import InferenceClient, InferenceSettings
from pydantic import Field

from iauto_foundry_agent.errors import FoundryAgentError
from iauto_foundry_agent.retrieval.base import Retriever, SearchHit
from iauto_foundry_agent.retrieval.factory import build_retriever
from iauto_foundry_agent.settings import FoundryAgentSettings

DEFAULT_INSTRUCTIONS = (
    "You are a grounded knowledge assistant migrated from a Copilot Studio bot. "
    "For any question that could be answered by company knowledge, you MUST call the "
    "`search_knowledge_base` tool first and base your answer only on the passages it "
    "returns. Cite the passage numbers you used like [1], [2]. If the knowledge base does "
    "not contain the answer, say you don't know and suggest contacting the relevant team. "
    "Be concise and never invent policy details."
)

_SEARCH_TOOL_DESCRIPTION = (
    "Search the company knowledge base for passages relevant to a question. "
    "Returns ranked, citation-ready passages. Call this before answering policy, "
    "how-to, or product questions."
)


def build_chat_client(
    inference: InferenceClient,
    inference_settings: InferenceSettings,
) -> OpenAIChatCompletionClient:
    """Wrap the modular-inference async client as an Agent Framework chat client.

    The provider (GitHub Models / Azure OpenAI / Foundry) is already resolved inside
    ``inference`` by ``INFERENCE_PROVIDER``; here we only borrow its OpenAI-compatible
    async transport and the matching model/deployment id.
    """
    model = inference_settings.default_model()
    if not model:
        raise FoundryAgentError(
            f"No model/deployment configured for provider "
            f"'{inference_settings.provider.value}'. Set the provider's model env var "
            f"(e.g. GITHUB_MODELS_MODEL / AZURE_OPENAI_DEPLOYMENT / AZURE_AI_FOUNDRY_MODEL)."
        )
    return OpenAIChatCompletionClient(async_client=inference.raw_async_client, model=model)


def format_context(hits: list[SearchHit]) -> str:
    """Render retrieved hits into a numbered, citation-friendly context block."""
    if not hits:
        return "No matching knowledge-base passages were found."
    blocks: list[str] = []
    for index, hit in enumerate(hits, start=1):
        citation = hit.document.source or hit.document.id
        blocks.append(
            f"[{index}] {hit.document.title} (source: {citation})\n{hit.document.content}"
        )
    return "\n\n".join(blocks)


def make_search_tool(retriever: Retriever, *, top_k: int = 4) -> Callable[[str], str]:
    """Build the ``search_knowledge_base`` function tool bound to ``retriever``.

    The returned callable's name, docstring, and annotations become the tool schema the
    model sees, so it can decide when to retrieve.
    """

    def search_knowledge_base(
        query: Annotated[str, Field(description="The user's question or search phrase.")],
    ) -> str:
        hits = retriever.search(query, top_k=top_k)
        return format_context(hits)

    search_knowledge_base.__doc__ = _SEARCH_TOOL_DESCRIPTION
    return search_knowledge_base


def build_agent(  # noqa: PLR0913 - explicit DI seams; every collaborator is injectable for tests
    *,
    retriever: Retriever | None = None,
    chat_client: OpenAIChatCompletionClient | None = None,
    inference: InferenceClient | None = None,
    inference_settings: InferenceSettings | None = None,
    agent_settings: FoundryAgentSettings | None = None,
    instructions: str | None = None,
    name: str | None = None,
    top_k: int | None = None,
) -> Agent:
    """Assemble a grounded :class:`~agent_framework.Agent`.

    All collaborators are injectable for testing; anything omitted is built from the
    environment. Pass ``chat_client`` (or ``inference``) to avoid touching a live provider.
    """
    resolved_settings = agent_settings or FoundryAgentSettings()

    if chat_client is None:
        resolved_inference_settings = inference_settings or InferenceSettings()
        resolved_inference = inference or InferenceClient(resolved_inference_settings)
        chat_client = build_chat_client(resolved_inference, resolved_inference_settings)

    if retriever is None:
        retriever = build_retriever(resolved_settings)

    resolved_top_k = top_k if top_k is not None else resolved_settings.retrieval_top_k
    tool = make_search_tool(retriever, top_k=resolved_top_k)
    resolved_instructions = (
        instructions or resolved_settings.agent_instructions or DEFAULT_INSTRUCTIONS
    )
    resolved_name = name or resolved_settings.agent_name

    return Agent(
        client=chat_client,
        instructions=resolved_instructions,
        name=resolved_name,
        tools=[tool],
    )


class GroundedKnowledgeAgent:
    """A retriever-backed agent with a one-call :meth:`ask` API.

    Holds both the framework :class:`~agent_framework.Agent` and its retriever so callers can
    answer questions *and* inspect the raw retrieved context (useful for evidence and debugging).
    """

    def __init__(self, agent: Agent, *, retriever: Retriever, top_k: int = 4) -> None:
        self._agent = agent
        self._retriever = retriever
        self._top_k = top_k

    @property
    def agent(self) -> Agent:
        """The underlying Agent Framework agent."""
        return self._agent

    @property
    def retriever(self) -> Retriever:
        """The retriever backing the RAG tool."""
        return self._retriever

    async def ask(self, question: str) -> str:
        """Answer ``question``, grounded in the knowledge base."""
        response = await self._agent.run(question)
        return response.text

    def search(self, query: str, *, top_k: int | None = None) -> list[SearchHit]:
        """Run the retriever directly (no model call) — handy for previews and evidence."""
        return self._retriever.search(query, top_k=top_k if top_k is not None else self._top_k)

    @classmethod
    def from_env(  # noqa: PLR0913 - explicit DI seams; collaborators are injectable for tests
        cls,
        *,
        agent_settings: FoundryAgentSettings | None = None,
        inference_settings: InferenceSettings | None = None,
        inference: InferenceClient | None = None,
        chat_client: OpenAIChatCompletionClient | None = None,
        retriever: Retriever | None = None,
        instructions: str | None = None,
        name: str | None = None,
        top_k: int | None = None,
    ) -> GroundedKnowledgeAgent:
        """Build a grounded agent from the environment, with optional injection for tests."""
        resolved_settings = agent_settings or FoundryAgentSettings()
        resolved_retriever = retriever or build_retriever(resolved_settings)
        resolved_top_k = top_k if top_k is not None else resolved_settings.retrieval_top_k
        agent = build_agent(
            retriever=resolved_retriever,
            chat_client=chat_client,
            inference=inference,
            inference_settings=inference_settings,
            agent_settings=resolved_settings,
            instructions=instructions,
            name=name,
            top_k=resolved_top_k,
        )
        return cls(agent, retriever=resolved_retriever, top_k=resolved_top_k)


async def answer(question: str, **kwargs: object) -> str:
    """Convenience: build a grounded agent from the environment and answer one question."""
    grounded = GroundedKnowledgeAgent.from_env(**kwargs)  # type: ignore[arg-type]
    return await grounded.ask(question)
