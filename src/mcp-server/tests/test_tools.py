"""Tests for the provider-agnostic tool coroutines using injected fake clients (no network)."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import pytest
from iauto_inference.settings import Provider
from iauto_mcp import tools
from iauto_mcp.models import EstateInventory, Passage

ClientFactory = Callable[..., Any]


async def test_summarize_document_returns_attributed_result(make_client: ClientFactory) -> None:
    client, completions = make_client(reply="A tight summary.", model="openai/gpt-4o-mini")
    result = await tools.summarize_document(client, text="Long source document.", max_words=50)
    assert result.text == "A tight summary."
    assert result.provider == "github"
    assert result.model == "openai/gpt-4o-mini"
    # The audience + word cap must reach the model and stay within budget.
    sent = completions.calls[0]
    assert sent["max_tokens"] <= 600
    assert "50 words" in sent["messages"][1]["content"]


async def test_summarize_document_strips_whitespace(make_client: ClientFactory) -> None:
    client, _ = make_client(reply="  padded  ")
    result = await tools.summarize_document(client, text="x")
    assert result.text == "padded"


async def test_draft_migration_plan_includes_constraints_and_sections(
    make_client: ClientFactory,
) -> None:
    client, completions = make_client(reply="## Overview\n...")
    await tools.draft_migration_plan(
        client, workload="Nightly approval flow", constraints="must finish in 2 weeks"
    )
    user_msg = completions.calls[0]["messages"][1]["content"]
    assert "must finish in 2 weeks" in user_msg
    assert "## Rollback" in user_msg


async def test_draft_migration_plan_omits_constraint_line_when_absent(
    make_client: ClientFactory,
) -> None:
    client, completions = make_client(reply="plan")
    await tools.draft_migration_plan(client, workload="Simple flow")
    assert "Hard constraints" not in completions.calls[0]["messages"][1]["content"]


async def test_estimate_discovery_sizing_with_narrative(make_client: ClientFactory) -> None:
    client, completions = make_client(reply="This is a medium estate...")
    result = await tools.estimate_discovery_sizing(
        client, inventory=EstateInventory(power_automate_flows=10, power_apps=5)
    )
    assert result.narrative == "This is a medium estate..."
    assert result.provider == "github"
    assert result.estimate.t_shirt_size in {"S", "M", "L", "XL"}
    assert completions.calls  # inference was invoked for the narrative


async def test_estimate_discovery_sizing_can_skip_inference(make_client: ClientFactory) -> None:
    client, completions = make_client(reply="should not be used")
    result = await tools.estimate_discovery_sizing(
        client, inventory=EstateInventory(power_apps=2), include_narrative=False
    )
    assert result.narrative is None
    assert result.provider is None
    assert completions.calls == []  # deterministic-only path: no network call


async def test_answer_with_context_grounds_and_counts_passages(
    make_client: ClientFactory,
) -> None:
    client, completions = make_client(reply="Azure Logic Apps [1].", provider=Provider.foundry)
    passages = [
        Passage(text="Logic Apps Standard is the landing target.", source="lab-3"),
        Passage(text="Functions handle code-first flows."),
    ]
    result = await tools.answer_with_context(
        client, question="Where do flows land?", passages=passages
    )
    assert result.passages_considered == 2
    assert result.provider == "foundry"
    grounding_system = completions.calls[0]["messages"][0]["content"]
    assert "only from the provided context" in grounding_system


async def test_answer_with_context_handles_no_passages(make_client: ClientFactory) -> None:
    client, completions = make_client(reply="I don't know based on the provided context.")
    result = await tools.answer_with_context(client, question="Anything?", passages=[])
    assert result.passages_considered == 0
    assert "no passages provided" in completions.calls[0]["messages"][1]["content"]


@pytest.mark.parametrize("temperature_key", ["temperature"])
async def test_grounded_answer_is_deterministic_temperature(
    make_client: ClientFactory, temperature_key: str
) -> None:
    client, completions = make_client(reply="x")
    await tools.answer_with_context(client, question="q", passages=[Passage(text="p")])
    assert completions.calls[0][temperature_key] == 0.0
