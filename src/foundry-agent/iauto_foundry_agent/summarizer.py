"""Provider-swappable context summarization via shared iauto_inference."""

from __future__ import annotations

from typing import Any, Protocol

from iauto_inference import ChatResult, InferenceClient

from iauto_foundry_agent.retrieval import RetrievalResult
from iauto_foundry_agent.telemetry import start_span

_SYSTEM_PROMPT = (
    "You summarize retrieved enterprise knowledge-base passages for a grounded RAG agent. "
    "Keep facts precise, preserve policy limits and steps, and include citation numbers like [1]. "
    "Do not add facts that are absent from the context."
)


class AsyncInferenceProtocol(Protocol):
    """Narrow async completion surface from iauto_inference."""

    async def acomplete(
        self,
        messages: object,
        *,
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        **extra: Any,
    ) -> ChatResult:
        """Return a normalized chat completion result."""
        ...


class ContextSummarizer:
    """Summarize retrieved context through the shared modular inference layer."""

    def __init__(self, client: AsyncInferenceProtocol | None = None) -> None:
        self._client = client or InferenceClient.from_env()

    async def summarize(self, question: str, retrieval: RetrievalResult) -> str:
        """Return a compact, citation-preserving summary of retrieved passages."""
        if not retrieval.chunks:
            return "No relevant knowledge-base passages were found."
        with start_span("inference.summarize_context") as span:
            span.set_attribute("retrieval.chunk_count", len(retrieval.chunks))
            result = await self._client.acomplete(
                [
                    {"role": "system", "content": _SYSTEM_PROMPT},
                    {
                        "role": "user",
                        "content": (
                            f"Question: {question}\n\n"
                            f"Retrieved context:\n{retrieval.format_context()}\n\n"
                            "Summarize only the facts needed to answer the question."
                        ),
                    },
                ],
                temperature=0.1,
                max_tokens=500,
            )
        return result.text.strip()
