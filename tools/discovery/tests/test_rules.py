"""Tests for the deterministic migration rules."""

from __future__ import annotations

from iauto_discovery import rules
from iauto_discovery.models import (
    AutomationType,
    EffortTShirt,
    InventoryItem,
    SizingTier,
)


def test_every_automation_type_has_a_target() -> None:
    for automation in AutomationType:
        item = InventoryItem(name="x", automation_type=automation)
        target, pattern, ref = rules.target_for(item)
        assert target
        assert pattern
        assert ref.startswith("Ref-Arch")


def test_sizing_tier_boundaries() -> None:
    assert rules.sizing_tier(0) is SizingTier.SMALL
    assert rules.sizing_tier(1_999) is SizingTier.SMALL
    assert rules.sizing_tier(2_000) is SizingTier.MEDIUM
    assert rules.sizing_tier(19_999) is SizingTier.MEDIUM
    assert rules.sizing_tier(20_000) is SizingTier.LARGE


def test_effort_minimal_is_small(simple_flow: InventoryItem) -> None:
    assert rules.effort_for(simple_flow) is EffortTShirt.S


def test_effort_maximal_is_xl(heavy_bot: InventoryItem) -> None:
    assert rules.effort_for(heavy_bot) is EffortTShirt.XL


def test_security_scales_with_sensitivity_and_onprem(heavy_bot: InventoryItem) -> None:
    recs = rules.security_recommendations(heavy_bot)
    joined = " ".join(recs)
    assert "Private Endpoints" in joined
    assert "Defender" in joined
    assert "on-prem" in joined.lower()


def test_security_minimal_has_identity_only(simple_flow: InventoryItem) -> None:
    recs = rules.security_recommendations(simple_flow)
    joined = " ".join(recs)
    assert "managed identity" in joined
    assert "Private Endpoints" not in joined
