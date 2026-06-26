"""Deterministic discovery & sizing heuristics -- no inference, no network, no I/O.

These functions turn a coarse Power Platform estate inventory into an Azure landing-zone
sizing estimate. They are intentionally simple and transparent so the numbers are
explainable in class: they are **planning aids**, not a substitute for the Power Platform
CoE toolkit, admin analytics, or the Azure pricing calculator. Because they are pure, they
are fully unit-tested without any provider.
"""

from __future__ import annotations

import math

from iauto_mcp.models import EstateInventory, SizingEstimate

# --- Complexity weights (higher == more migration effort per unit) ---
_W_FLOW = 1.0
_W_APP = 1.5
_W_TABLE = 0.5
_W_CONNECTOR = 2.0
_RUNS_PER_SCORE_POINT = 10_000
_GB_PER_SCORE_POINT = 10.0

# --- Effort model (person-days) ---
_BASE_EFFORT_DAYS = 3.0
_EFFORT_FLOW = 0.5
_EFFORT_APP = 1.0
_EFFORT_TABLE = 0.25
_EFFORT_CONNECTOR = 0.5

# A flow typically performs several billable actions per run (Logic Apps fan-out).
_ACTIONS_PER_RUN = 6
_SECONDS_PER_HOUR = 3600

# --- T-shirt thresholds on the complexity score ---
_SIZE_THRESHOLDS: tuple[tuple[float, str], ...] = ((10.0, "S"), (30.0, "M"), (75.0, "L"))
_SIZE_XL = "XL"

# Indicative monthly run-cost bands on Azure (USD, planning only).
_COST_BANDS = {
    "S": "$50-150 / month",
    "M": "$150-600 / month",
    "L": "$600-2,000 / month",
    "XL": "$2,000+ / month",
}

# Power Platform component -> recommended Azure landing service.
_RECOMMENDED_TARGETS = {
    "Power Automate cloud flows": "Azure Logic Apps (Standard) or Azure Functions",
    "Power Apps": "Azure App Service / Static Web Apps + Azure Functions",
    "Dataverse tables": "Azure SQL Database or Azure Cosmos DB",
    "Premium / custom connectors": "Azure API Management + Logic Apps connectors",
    "AI Builder / Copilot": "Azure AI Foundry / Azure OpenAI via modular inference",
}


def _t_shirt_size(score: float) -> str:
    """Map a complexity score onto a relative S/M/L/XL band."""
    for threshold, label in _SIZE_THRESHOLDS:
        if score < threshold:
            return label
    return _SIZE_XL


def estimate_sizing(inventory: EstateInventory) -> SizingEstimate:
    """Compute a transparent, deterministic sizing estimate from an estate inventory."""
    score = (
        inventory.power_automate_flows * _W_FLOW
        + inventory.power_apps * _W_APP
        + inventory.dataverse_tables * _W_TABLE
        + inventory.premium_connectors * _W_CONNECTOR
        + inventory.monthly_runs / _RUNS_PER_SCORE_POINT
        + inventory.data_gb / _GB_PER_SCORE_POINT
    )
    size = _t_shirt_size(score)
    effort_days = (
        _BASE_EFFORT_DAYS
        + inventory.power_automate_flows * _EFFORT_FLOW
        + inventory.power_apps * _EFFORT_APP
        + inventory.dataverse_tables * _EFFORT_TABLE
        + inventory.premium_connectors * _EFFORT_CONNECTOR
    )
    compute_hours = inventory.monthly_runs * inventory.avg_run_seconds / _SECONDS_PER_HOUR
    return SizingEstimate(
        t_shirt_size=size,
        complexity_score=round(score, 2),
        monthly_action_executions=inventory.monthly_runs * _ACTIONS_PER_RUN,
        monthly_compute_hours=round(compute_hours, 2),
        effort_person_days=math.ceil(effort_days),
        recommended_targets=dict(_RECOMMENDED_TARGETS),
        indicative_monthly_cost_band_usd=_COST_BANDS[size],
        assumptions=[
            f"Assumes ~{_ACTIONS_PER_RUN} billable actions per flow run.",
            "Cost band is a planning placeholder, not an Azure pricing quote.",
            "Validate run counts and durations with Power Platform admin analytics or the CoE kit.",
            "Effort excludes organisational change management and security review.",
        ],
    )
