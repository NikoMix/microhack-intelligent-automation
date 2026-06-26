"""Discovery, sizing, and migration decisioning for Power Platform → Azure.

Module B.1.2 lab artifact. Deterministic, offline-by-default rules with an optional
LLM-generated executive narrative via the shared modular inference layer.
"""

from __future__ import annotations

from iauto_discovery.engine import assess_item, build_report
from iauto_discovery.models import (
    AutomationType,
    Complexity,
    DiscoveryReport,
    InventoryItem,
    ItemAssessment,
    PortfolioSummary,
    RoiAssumptions,
    Sensitivity,
)

__all__ = [
    "AutomationType",
    "Complexity",
    "DiscoveryReport",
    "InventoryItem",
    "ItemAssessment",
    "PortfolioSummary",
    "RoiAssumptions",
    "Sensitivity",
    "assess_item",
    "build_report",
]

__version__ = "0.1.0"
