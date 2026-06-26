"""Stdio entry point and FastMCP wiring for the intelligent-automation MCP server.

This module is intentionally thin: it declares the tool *surface* (names, signatures, and
docstrings that become the MCP schema) and delegates all behaviour to :mod:`iauto_mcp.tools`.
Tools resolve the shared inference client lazily via ``inference.get_client()`` -- accessed
through the module so tests can substitute a fake-backed client.

Run it directly (stdio is the default transport)::

    uv run iauto-mcp-server
    # or:  uv run mcp dev iauto_mcp/server.py   # opens the MCP Inspector (needs mcp[cli])
"""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from iauto_mcp import inference, tools
from iauto_mcp.models import (
    EstateInventory,
    GroundedAnswer,
    InferenceToolResult,
    Passage,
    SizingResult,
)
from iauto_mcp.telemetry import setup_telemetry, traced

mcp = FastMCP("iauto-intelligent-automation")


@mcp.tool()
async def summarize_document(
    text: str,
    max_words: int = 120,
    audience: str = "a technical migration lead",
) -> InferenceToolResult:
    """Summarise a document or snippet for an audience.

    The unattended document-intelligence target from Lab 3. Runs on the active inference
    provider (GitHub Models, Azure OpenAI, or Azure AI Foundry) chosen by configuration.
    """
    with traced("tool.summarize_document", max_words=max_words):
        return await tools.summarize_document(
            inference.get_client(), text=text, max_words=max_words, audience=audience
        )


@mcp.tool()
async def draft_migration_plan(
    workload: str,
    source_platform: str = "Power Platform",
    target_cloud: str = "Azure",
    constraints: str | None = None,
) -> InferenceToolResult:
    """Draft a structured Power Platform -> Azure migration plan for a described workload."""
    with traced("tool.draft_migration_plan"):
        return await tools.draft_migration_plan(
            inference.get_client(),
            workload=workload,
            source_platform=source_platform,
            target_cloud=target_cloud,
            constraints=constraints,
        )


@mcp.tool()
async def estimate_discovery_sizing(
    inventory: EstateInventory,
    include_narrative: bool = True,
) -> SizingResult:
    """Estimate Azure landing-zone sizing and effort for a Power Platform estate (Lab 1)."""
    with traced("tool.estimate_discovery_sizing", include_narrative=include_narrative):
        return await tools.estimate_discovery_sizing(
            inference.get_client(), inventory=inventory, include_narrative=include_narrative
        )


@mcp.tool()
async def answer_with_context(question: str, passages: list[Passage]) -> GroundedAnswer:
    """Answer a question grounded strictly in the supplied context passages (Lab 4 RAG)."""
    with traced("tool.answer_with_context", passages=len(passages)):
        return await tools.answer_with_context(
            inference.get_client(), question=question, passages=passages
        )


def main() -> None:
    """Console-script entry point: configure optional telemetry, then serve over stdio."""
    setup_telemetry()
    mcp.run()


if __name__ == "__main__":  # pragma: no cover
    main()
