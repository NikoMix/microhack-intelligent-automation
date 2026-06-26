"""Provider-agnostic tool logic for the intelligent-automation MCP server.

Each coroutine accepts an injected :class:`iauto_inference.InferenceClient`, so the MCP
transport layer (:mod:`iauto_mcp.server`) stays thin and these functions remain unit-testable
with fake clients -- no network, no provider lock-in. Switching between **GitHub Models**,
**Azure OpenAI**, and **Azure AI Foundry** is a configuration change handled entirely inside
the client, never here.
"""

from __future__ import annotations

from iauto_inference import ChatMessage, ChatResult, InferenceClient

from iauto_mcp.models import (
    EstateInventory,
    GroundedAnswer,
    InferenceToolResult,
    Passage,
    SizingResult,
)
from iauto_mcp.sizing import estimate_sizing

# Generation caps keep classroom usage cheap and responses tight.
_SUMMARY_TOKEN_BUDGET = 600
_PLAN_TOKEN_BUDGET = 1200
_SIZING_TOKEN_BUDGET = 500
_RAG_TOKEN_BUDGET = 600

_FOCUSED_TEMPERATURE = 0.2
_GROUNDED_TEMPERATURE = 0.0

# Exact phrase the RAG tool must emit when the context does not support an answer.
_GROUNDING_REFUSAL = "I don't know based on the provided context."


def _to_result(completion: ChatResult) -> InferenceToolResult:
    """Project a normalised :class:`ChatResult` onto the tool's output model."""
    return InferenceToolResult(
        text=completion.text.strip(),
        provider=completion.provider,
        model=completion.model,
        prompt_tokens=completion.prompt_tokens,
        completion_tokens=completion.completion_tokens,
    )


async def summarize_document(
    client: InferenceClient,
    *,
    text: str,
    max_words: int = 120,
    audience: str = "a technical migration lead",
) -> InferenceToolResult:
    """Summarise a document faithfully for a target audience (Lab 3 doc-intel target)."""
    system = (
        "You are an expert technical writer for intelligent-automation and cloud-migration "
        "projects. You produce faithful, concise summaries and never invent facts that are "
        "not present in the source."
    )
    user = (
        f"Summarise the document below for {audience} in at most {max_words} words. Lead with "
        "the single most important point, then the key details as tight bullet points. "
        "Preserve concrete names, numbers, and decisions.\n\n--- DOCUMENT ---\n"
        f"{text}"
    )
    completion = await client.acomplete(
        [ChatMessage(role="system", content=system), ChatMessage(role="user", content=user)],
        temperature=_FOCUSED_TEMPERATURE,
        max_tokens=_SUMMARY_TOKEN_BUDGET,
    )
    return _to_result(completion)


async def draft_migration_plan(
    client: InferenceClient,
    *,
    workload: str,
    source_platform: str = "Power Platform",
    target_cloud: str = "Azure",
    constraints: str | None = None,
) -> InferenceToolResult:
    """Draft a structured, buildable migration plan for a workload."""
    system = (
        "You are an Azure migration architect who moves Power Platform workloads to Azure "
        "PaaS. You give specific, buildable, well-structured plans grounded in Azure "
        "Well-Architected best practices, and you default to free/consumption tiers."
    )
    constraint_line = f"\nHard constraints to honour: {constraints}" if constraints else ""
    user = (
        f"Draft a concise plan to migrate this {source_platform} workload to {target_cloud}."
        f"{constraint_line}\n\nWorkload:\n{workload}\n\n"
        "Use exactly these Markdown sections: ## Overview, ## Target architecture, "
        "## Migration steps, ## Risks & mitigations, ## Validation, ## Rollback. For any AI "
        "capability, prefer modular, provider-agnostic inference (GitHub Models / Azure "
        "OpenAI / Azure AI Foundry, selected by configuration)."
    )
    completion = await client.acomplete(
        [ChatMessage(role="system", content=system), ChatMessage(role="user", content=user)],
        temperature=_FOCUSED_TEMPERATURE,
        max_tokens=_PLAN_TOKEN_BUDGET,
    )
    return _to_result(completion)


async def estimate_discovery_sizing(
    client: InferenceClient,
    *,
    inventory: EstateInventory,
    include_narrative: bool = True,
) -> SizingResult:
    """Produce a deterministic sizing estimate plus an optional AI narrative (Lab 1)."""
    estimate = estimate_sizing(inventory)
    if not include_narrative:
        return SizingResult(estimate=estimate)
    system = (
        "You are an Azure migration architect explaining a discovery & sizing estimate to a "
        "stakeholder. Be concrete and honest about uncertainty; never invent numbers."
    )
    user = (
        "Explain this Power Platform -> Azure sizing estimate in 4-6 sentences: what the size "
        "band implies, the main Azure landing services, and the biggest driver of effort. Use "
        "only the figures provided.\n\n"
        f"Inventory: {inventory.model_dump_json()}\nEstimate: {estimate.model_dump_json()}"
    )
    completion = await client.acomplete(
        [ChatMessage(role="system", content=system), ChatMessage(role="user", content=user)],
        temperature=_FOCUSED_TEMPERATURE,
        max_tokens=_SIZING_TOKEN_BUDGET,
    )
    return SizingResult(
        estimate=estimate,
        narrative=completion.text.strip(),
        provider=completion.provider,
        model=completion.model,
    )


async def answer_with_context(
    client: InferenceClient,
    *,
    question: str,
    passages: list[Passage],
) -> GroundedAnswer:
    """Answer a question grounded strictly in supplied passages (Lab 4 RAG pattern)."""
    numbered = "\n\n".join(
        f"[{index}] {passage.text}" + (f"  (source: {passage.source})" if passage.source else "")
        for index, passage in enumerate(passages, start=1)
    )
    system = (
        "You answer strictly and only from the provided context passages. If the answer is "
        "not fully supported by the context, reply with exactly: "
        f"'{_GROUNDING_REFUSAL}'. Cite supporting passages inline as [n]."
    )
    user = f"Context:\n{numbered or '(no passages provided)'}\n\nQuestion: {question}"
    completion = await client.acomplete(
        [ChatMessage(role="system", content=system), ChatMessage(role="user", content=user)],
        temperature=_GROUNDED_TEMPERATURE,
        max_tokens=_RAG_TOKEN_BUDGET,
    )
    return GroundedAnswer(
        answer=completion.text.strip(),
        passages_considered=len(passages),
        provider=completion.provider,
        model=completion.model,
    )
