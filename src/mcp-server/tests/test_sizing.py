"""Unit tests for the pure, deterministic sizing heuristics (no inference, no network)."""

from __future__ import annotations

from iauto_mcp.models import EstateInventory
from iauto_mcp.sizing import estimate_sizing


def test_empty_estate_is_small() -> None:
    estimate = estimate_sizing(EstateInventory())
    assert estimate.t_shirt_size == "S"
    assert estimate.complexity_score == 0.0
    assert estimate.effort_person_days >= 3  # base effort floor
    assert estimate.recommended_targets  # always non-empty guidance


def test_size_bands_increase_with_estate() -> None:
    small = estimate_sizing(EstateInventory(power_automate_flows=2))
    large = estimate_sizing(
        EstateInventory(power_automate_flows=40, power_apps=20, premium_connectors=15)
    )
    assert small.complexity_score < large.complexity_score
    assert large.t_shirt_size in {"L", "XL"}


def test_connectors_weigh_more_than_tables() -> None:
    connectors = estimate_sizing(EstateInventory(premium_connectors=10))
    tables = estimate_sizing(EstateInventory(dataverse_tables=10))
    assert connectors.complexity_score > tables.complexity_score


def test_compute_hours_track_runs_and_duration() -> None:
    estimate = estimate_sizing(EstateInventory(monthly_runs=3600, avg_run_seconds=10))
    # 3600 runs * 10s = 36000s = 10 compute-hours.
    assert estimate.monthly_compute_hours == 10.0


def test_action_executions_fan_out_from_runs() -> None:
    estimate = estimate_sizing(EstateInventory(monthly_runs=1000))
    assert estimate.monthly_action_executions == 6000


def test_estimate_is_serialisable() -> None:
    payload = estimate_sizing(EstateInventory(power_apps=3)).model_dump()
    assert set(payload) >= {
        "t_shirt_size",
        "complexity_score",
        "effort_person_days",
        "recommended_targets",
        "assumptions",
    }
