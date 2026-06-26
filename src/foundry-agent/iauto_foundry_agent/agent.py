"""Microsoft Agent Framework orchestration for the Lab 4 RAG agent."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Annotated, Any, Protocol, cast

from agent_framework import Agent, tool
from agent_framework.foundry import FoundryChatClient
from agent_framework.openai import OpenAIChatCompletionClient
from azure.identity import DefaultAzureCredential
from iauto_inference import InferenceClient, InferenceConfigError, InferenceSettings
from pydantic import Field

from iauto_foundry_agent.retrieval import AzureSearchRetriever, RetrievalResult
from iauto_foundry_agent.settings import Settings
from iauto_foundry_agent.summarizer import ContextSummarizer
from iauto_foundry_agent.telemetry import start_span

_TOOL_DESCRIPTION = "Search the migrated internal knowledge base and return grounded citations."
_AGENT_INSTRUCTIONS = (
    "You are the Azure AI Foundry replacement for a Copilot Studio knowledge agent. "
    "Answer only from provided Azure AI Search context or the search_knowledge_base tool. "
    "Use concise language, state when evidence is missing, and cite every factual claim "
    "with citation numbers like [1] that map to the supplied citation list."
)


class AgentRunnerProtocol(Protocol):
    """Narrow Agent Framework run surface, mockable in tests."""

    def run(self, messages: str, **kwargs: Any) -> Awaitable[Any]:
        """Run one agent turn."""
        ...


AgentFactory = Callable[[AzureSearchRetriever], AgentRunnerProtocol]


@dataclass(frozen=True, slots=True)
class GroundedAnswer:
    """Agent answer plus the evidence used to ground it."""

    question: str
    answer: str
    retrieval: RetrievalResult
    context_summary: str
    runtime: str

    def format_for_cli(self) -> str:
        return (
            f"Answer:\n{self.answer}\n\n"
            f"Citations:\n{self.retrieval.format_citations()}\n\n"
            f"Context summary ({self.runtime} modular helper):\n{self.context_summary}"
        )


def make_retrieval_tool(retriever: AzureSearchRetriever) -> Callable[[str], Awaitable[str]]:
    """Expose Azure AI Search retrieval as an Agent Framework function tool."""

    @tool(approval_mode="never_require")
    async def search_knowledge_base(
        query: Annotated[str, Field(description="The user's knowledge-base search query.")],
    ) -> str:
        """Search the migrated internal knowledge base."""
        result = await retriever.retrieve(query)
        return result.format_context()

    search_knowledge_base.__doc__ = _TOOL_DESCRIPTION
    return search_knowledge_base


class FoundryRagAgent:
    """RAG runner using Agent Framework, Azure AI Search, and iauto_inference.

    Boundary: the default ``modular`` runtime gives Agent Framework an OpenAI-compatible
    async client from ``iauto_inference`` so GitHub Models, Azure OpenAI, or Foundry can be
    swapped by environment. The optional ``foundry`` runtime uses Agent Framework's native
    ``FoundryChatClient`` because Foundry project endpoints require that client; the retrieved
    context summarizer still uses ``iauto_inference`` to keep the provider-swappable story visible.
    """

    def __init__(
        self,
        settings: Settings,
        retriever: AzureSearchRetriever,
        summarizer: ContextSummarizer,
        *,
        agent_factory: AgentFactory | None = None,
    ) -> None:
        self._settings = settings
        self._retriever = retriever
        self._summarizer = summarizer
        self._agent_factory = agent_factory or self._build_agent

    async def answer(self, question: str) -> GroundedAnswer:
        """Retrieve, summarize, then ask the Agent Framework runtime for a cited answer."""
        with start_span("agent.answer") as span:
            span.set_attribute("agent.runtime", self._settings.agent_runtime)
            retrieval = await self._retriever.retrieve(question)
            summary = await self._summarizer.summarize(question, retrieval)
            prompt = self._build_prompt(question, retrieval, summary)
            agent = self._agent_factory(self._retriever)
            response = await agent.run(prompt)
            answer = _response_text(response)
        return GroundedAnswer(
            question=question,
            answer=answer,
            retrieval=retrieval,
            context_summary=summary,
            runtime=self._settings.agent_runtime,
        )

    def _build_agent(self, retriever: AzureSearchRetriever) -> AgentRunnerProtocol:
        if self._settings.agent_runtime == "foundry":
            return self._build_foundry_agent(retriever)
        return self._build_modular_agent(retriever)

    def _build_modular_agent(self, retriever: AzureSearchRetriever) -> AgentRunnerProtocol:
        inference_settings = InferenceSettings()
        model = inference_settings.default_model()
        if not model:
            msg = "No model configured for the selected INFERENCE_PROVIDER."
            raise InferenceConfigError(msg)
        inference_client = InferenceClient(inference_settings)
        chat_client = OpenAIChatCompletionClient(
            model=model,
            async_client=inference_client.raw_async_client,
        )
        return cast(
            AgentRunnerProtocol,
            chat_client.as_agent(
                name="PowerPlatformToAzureKnowledgeAgent",
                instructions=_AGENT_INSTRUCTIONS,
                tools=[make_retrieval_tool(retriever)],
            ),
        )

    def _build_foundry_agent(self, retriever: AzureSearchRetriever) -> AgentRunnerProtocol:
        if not self._settings.foundry_project_endpoint:
            msg = "Set AZURE_AI_FOUNDRY_PROJECT_ENDPOINT for IAUTO_AGENT_RUNTIME=foundry."
            raise ValueError(msg)
        client = FoundryChatClient(
            project_endpoint=self._settings.foundry_project_endpoint,
            model=self._settings.foundry_model,
            credential=DefaultAzureCredential(),
        )
        return cast(
            AgentRunnerProtocol,
            Agent(
                client=client,
                name="PowerPlatformToAzureKnowledgeAgent",
                instructions=_AGENT_INSTRUCTIONS,
                tools=[make_retrieval_tool(retriever)],
            ),
        )

    @staticmethod
    def _build_prompt(question: str, retrieval: RetrievalResult, summary: str) -> str:
        return (
            f"Question:\n{question}\n\n"
            f"Retrieved Azure AI Search context:\n{retrieval.format_context()}\n\n"
            f"Citation map:\n{retrieval.format_citations()}\n\n"
            f"Provider-swappable context summary from iauto_inference:\n{summary}\n\n"
            "Write the final grounded answer. If context is insufficient, say so."
        )


def _response_text(response: object) -> str:
    text = getattr(response, "text", None)
    if isinstance(text, str) and text.strip():
        return text.strip()
    return str(response).strip()
