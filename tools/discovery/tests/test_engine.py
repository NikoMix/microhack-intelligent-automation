"""Tests for the assessment engine and ROI aggregation."""

from __future__ import annotations

from iauto_discovery.engine import assess_item, build_report
from iauto_discovery.models import (
    AutomationType,
    Complexity,
    EffortTShirt,
    InventoryItem,
    RoiAssumptions,
    SizingTier,
)


def test_assess_item_sizes_and_costs(simple_flow: InventoryItem) -> None:
    a = assess_item(simple_flow)
    # 10 runs * 2 min * 21 working days = 420 minutes/month.
    assert a.monthly_execution_minutes == 420.0
    assert a.sizing_tier is SizingTier.SMALL
    assert a.effort is EffortTShirt.S
    assert a.indicative_monthly_cost_usd == 15.0
    assert a.notes[0].startswith("Ref-Arch")


def test_assess_item_flags_premium(heavy_bot: InventoryItem) -> None:
    a = assess_item(heavy_bot)
    assert any("premium" in note.lower() for note in a.notes)
    assert a.sizing_tier is SizingTier.LARGE


def test_zero_runrate_defaults_small_with_note() -> None:
    item = InventoryItem(name="idle", automation_type=AutomationType.CLOUD_FLOW)
    a = assess_item(item)
    assert a.sizing_tier is SizingTier.SMALL
    assert any("No run-rate" in note for note in a.notes)


def test_build_report_aggregates(simple_flow: InventoryItem, heavy_bot: InventoryItem) -> None:
    report = build_report([simple_flow, heavy_bot])
    s = report.summary
    assert s.total_items == 2
    assert s.total_indicative_monthly_cost_usd == 315.0  # 15 + 300
    assert s.by_effort == {"S": 1, "XL": 1}
    assert len(s.by_target) == 2
    # Premium avoided is only the heavy bot (default $15); azure cost dwarfs it.
    assert s.estimated_monthly_pp_savings_usd == 15.0
    assert s.estimated_payback_months is None  # net saving is negative


def test_payback_when_savings_exceed_cost() -> None:
    item = InventoryItem(
        name="cheap premium flow",
        automation_type=AutomationType.CLOUD_FLOW,
        runs_per_day=1,
        avg_minutes=1,
        complexity=Complexity.LOW,
        premium_licensed=True,
    )
    assumptions = RoiAssumptions(pp_premium_monthly=100, azure_cost_small=15, effort_cost_s=2000)
    report = build_report([item], assumptions)
    s = report.summary
    # net monthly saving = 100 - 15 = 85; payback = 2000 / 85 = 23.5 months.
    assert s.estimated_payback_months == 23.5
