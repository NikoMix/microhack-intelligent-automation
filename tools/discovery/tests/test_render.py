"""Tests for Markdown / JSON rendering."""

from __future__ import annotations

import json

from iauto_discovery.engine import build_report
from iauto_discovery.models import InventoryItem
from iauto_discovery.render import to_json, to_markdown


def _report(simple_flow: InventoryItem, heavy_bot: InventoryItem) -> object:
    return build_report([simple_flow, heavy_bot])


def test_markdown_has_sections(simple_flow: InventoryItem, heavy_bot: InventoryItem) -> None:
    md = to_markdown(_report(simple_flow, heavy_bot))  # type: ignore[arg-type]
    assert md.startswith("# Discovery & sizing report")
    assert "## Portfolio summary" in md
    assert "| Automation | Type | Azure target |" in md
    assert "Evidence awareness" in md
    assert simple_flow.name in md
    assert heavy_bot.name in md


def test_markdown_includes_narrative_when_present(
    simple_flow: InventoryItem, heavy_bot: InventoryItem
) -> None:
    report = build_report([simple_flow, heavy_bot])
    report.narrative = "Migrate quick wins first."
    md = to_markdown(report)
    assert "## Executive narrative" in md
    assert "Migrate quick wins first." in md


def test_json_round_trips(simple_flow: InventoryItem, heavy_bot: InventoryItem) -> None:
    report = build_report([simple_flow, heavy_bot])
    payload = json.loads(to_json(report))
    assert payload["summary"]["total_items"] == 2
    assert len(payload["assessments"]) == 2
