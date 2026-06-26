"""Tests for the FastMCP wiring: tool registration, schemas, and end-to-end dispatch.

These tests drive the server through its public MCP surface (``list_tools`` / ``call_tool``)
while monkeypatching the lazy client factory, so no provider or network is touched.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import pytest
from iauto_mcp import inference, server
from iauto_mcp.models import EstateInventory

ClientFactory = Callable[..., Any]

EXPECTED_TOOLS = {
    "summarize_document",
    "draft_migration_plan",
    "estimate_discovery_sizing",
    "answer_with_context",
}


async def test_server_registers_all_tools() -> None:
    registered = {tool.name for tool in await server.mcp.list_tools()}
    assert registered == EXPECTED_TOOLS


async def test_tools_expose_input_and_output_schemas() -> None:
    for tool in await server.mcp.list_tools():
        assert tool.description, f"{tool.name} is missing a description"
        assert tool.inputSchema, f"{tool.name} is missing an input schema"
        # Pydantic return models give MCP a structured output schema clients can validate.
        assert tool.outputSchema is not None, f"{tool.name} is missing an output schema"


async def test_call_summarize_document_through_server(
    make_client: ClientFactory, monkeypatch: pytest.MonkeyPatch
) -> None:
    client, _ = make_client(reply="Server-routed summary.")
    monkeypatch.setattr(inference, "get_client", lambda: client)
    result = await server.summarize_document(text="Document body", max_words=40)
    assert result.text == "Server-routed summary."
    assert result.provider == "github"


async def test_call_sizing_through_server_without_inference(
    make_client: ClientFactory, monkeypatch: pytest.MonkeyPatch
) -> None:
    client, completions = make_client(reply="unused")
    monkeypatch.setattr(inference, "get_client", lambda: client)
    result = await server.estimate_discovery_sizing(
        inventory=EstateInventory(power_automate_flows=4), include_narrative=False
    )
    assert result.estimate.t_shirt_size in {"S", "M", "L", "XL"}
    assert completions.calls == []


async def test_call_tool_returns_structured_content(
    make_client: ClientFactory, monkeypatch: pytest.MonkeyPatch
) -> None:
    client, _ = make_client(reply="Routed via call_tool.")
    monkeypatch.setattr(inference, "get_client", lambda: client)
    _content, structured = await server.mcp.call_tool(
        "summarize_document", {"text": "Body", "max_words": 30}
    )
    assert isinstance(structured, dict)
    assert structured["text"] == "Routed via call_tool."
    assert structured["provider"] == "github"
