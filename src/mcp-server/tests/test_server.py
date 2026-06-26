from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pytest
from iauto_mcp.models import AutomationInventoryItem
from iauto_mcp.server import (
    assess_migration,
    estimate_roi,
    recommend_azure_target,
    summarize_inventory,
)


def _cloud_flow() -> AutomationInventoryItem:
    return AutomationInventoryItem.model_validate(
        {
            "name": "Invoice approval flow",
            "type": "cloud_flow",
            "runs/day": 120,
            "avg_minutes": 2.5,
            "connectors": ["SharePoint", "Outlook", "Dataverse"],
            "complexity": "medium",
            "sensitivity": "medium",
            "premium_licensed": True,
        }
    )


@pytest.mark.asyncio
async def test_assess_migration_uses_discovery_engine() -> None:
    response = await assess_migration(_cloud_flow())

    assert response.ok is True
    assert response.data is not None
    assert response.data.azure_target == "Azure Logic Apps Standard"
    assert response.data.sizing_tier.value == "medium"
    assert response.data.monthly_execution_minutes == 6300
    assert "Private Endpoints" in " ".join(response.data.security_recommendations)


@pytest.mark.asyncio
async def test_recommend_azure_target_returns_reference_architecture() -> None:
    response = await recommend_azure_target("ai_builder_doc", sensitivity="high")

    assert response.ok is True
    assert response.data is not None
    assert response.data.azure_target == "Azure AI Document Intelligence + Azure Functions"
    assert response.data.reference_architecture == "Ref-Arch 4: Document processing"
    assert any("Defender" in rec for rec in response.data.default_security_recommendations)


@dataclass(frozen=True)
class _FakeResult:
    text: str
    model: str
    provider: str


class _FakeClient:
    async def acomplete(self, messages: Any, **kwargs: Any) -> _FakeResult:
        assert kwargs["temperature"] == 0.2
        assert kwargs["max_tokens"] == 650
        assert messages[0]["role"] == "system"
        assert "Discovery report JSON" in messages[1]["content"]
        return _FakeResult(
            text="Executive summary: migrate quick-win flows first.",
            model="fake-model",
            provider="fake-provider",
        )


class _FakeInferenceClient:
    @classmethod
    def from_env(cls) -> _FakeClient:
        return _FakeClient()


@pytest.mark.asyncio
async def test_summarize_inventory_uses_shared_inference_layer(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("iauto_mcp.server.InferenceClient", _FakeInferenceClient)

    response = await summarize_inventory([_cloud_flow()])

    assert response.ok is True
    assert response.data is not None
    assert response.data.report.summary.total_items == 1
    assert response.data.executive_summary == "Executive summary: migrate quick-win flows first."
    assert response.data.inference_provider == "fake-provider"
    assert response.data.inference_model == "fake-model"


@pytest.mark.asyncio
async def test_estimate_roi_surfaces_discovery_roi() -> None:
    response = await estimate_roi([_cloud_flow()])

    assert response.ok is True
    assert response.data is not None
    assert response.data.total_items == 1
    assert response.data.total_indicative_monthly_cost_usd == 75
    assert response.data.estimated_total_migration_cost_usd == 6000
    assert response.data.interpretation == "no-positive-payback"


@pytest.mark.asyncio
async def test_empty_inventory_returns_structured_error() -> None:
    response = await estimate_roi([])

    assert response.ok is False
    assert response.error is not None
    assert response.error.code == "validation_error"
