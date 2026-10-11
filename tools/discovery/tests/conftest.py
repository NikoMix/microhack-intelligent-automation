"""Shared fixtures for the discovery tool tests."""

from __future__ import annotations

import pytest
from iauto_discovery.models import (
    AutomationType,
    Complexity,
    InventoryItem,
    Sensitivity,
)


@pytest.fixture
def simple_flow() -> InventoryItem:
    """A small, low-risk cloud flow → smallest tier, S effort."""
    return InventoryItem(
        name="Lead routing flow",
        automation_type=AutomationType.CLOUD_FLOW,
        runs_per_day=10,
        avg_minutes=2,
        connectors=2,
        complexity=Complexity.LOW,
        data_sensitivity=Sensitivity.LOW,
        on_prem_dependency=False,
        premium_licensed=False,
    )


@pytest.fixture
def heavy_bot() -> InventoryItem:
    """A high-complexity Copilot Studio bot → heavy effort, sensitive."""
    return InventoryItem(
        name="Sales assistant chatbot",
        automation_type=AutomationType.COPILOT_STUDIO,
        runs_per_day=500,
        avg_minutes=2,
        connectors=6,
        complexity=Complexity.HIGH,
        data_sensitivity=Sensitivity.HIGH,
        on_prem_dependency=True,
        premium_licensed=True,
    )
