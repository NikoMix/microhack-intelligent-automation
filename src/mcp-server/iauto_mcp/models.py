"""Typed MCP tool contracts for the intelligent-automation migration server."""

from __future__ import annotations

from typing import Literal

from iauto_discovery.models import (
    AutomationType,
    Complexity,
    DiscoveryReport,
    InventoryItem,
    ItemAssessment,
    Sensitivity,
)
from pydantic import AliasChoices, BaseModel, ConfigDict, Field, field_validator


class AutomationInventoryItem(BaseModel):
    """External tool input for one Power Platform automation inventory item."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    name: str = Field(min_length=1, max_length=160)
    automation_type: AutomationType = Field(
        validation_alias=AliasChoices("automation_type", "type"),
        description="Power Platform automation type, for example cloud_flow.",
    )
    runs_per_day: float = Field(
        default=0,
        ge=0,
        validation_alias=AliasChoices("runs_per_day", "runs/day"),
    )
    avg_minutes: float = Field(default=0, ge=0)
    connectors: int | list[str] = Field(
        default=0,
        description="Connector count or connector names. Names are counted for sizing.",
    )
    complexity: Complexity = Complexity.MEDIUM
    data_sensitivity: Sensitivity = Field(
        default=Sensitivity.LOW,
        validation_alias=AliasChoices("data_sensitivity", "sensitivity"),
    )
    on_prem_dependency: bool = False
    premium_licensed: bool = False

    @field_validator("connectors")
    @classmethod
    def _validate_connectors(cls, value: int | list[str]) -> int | list[str]:
        if isinstance(value, int) and value < 0:
            msg = "connectors must be a non-negative count or a list of connector names."
            raise ValueError(msg)
        if isinstance(value, list) and any(not connector.strip() for connector in value):
            msg = "connector names must be non-empty strings."
            raise ValueError(msg)
        return value

    def to_discovery_item(self) -> InventoryItem:
        """Convert the public MCP contract to the shared discovery engine model."""
        connector_count = (
            len(self.connectors) if isinstance(self.connectors, list) else self.connectors
        )
        return InventoryItem(
            name=self.name,
            automation_type=self.automation_type,
            runs_per_day=self.runs_per_day,
            avg_minutes=self.avg_minutes,
            connectors=connector_count,
            complexity=self.complexity,
            data_sensitivity=self.data_sensitivity,
            on_prem_dependency=self.on_prem_dependency,
            premium_licensed=self.premium_licensed,
        )


class ToolError(BaseModel):
    """Structured error payload returned instead of crashing an MCP tool."""

    code: str
    message: str
    details: list[str] = Field(default_factory=list)


class AssessmentResponse(BaseModel):
    """Response from assess_migration."""

    ok: bool
    data: ItemAssessment | None = None
    error: ToolError | None = None


class TargetRecommendation(BaseModel):
    """Azure landing recommendation for an automation type."""

    automation_type: AutomationType
    azure_target: str
    migration_pattern: str
    reference_architecture: str
    default_security_recommendations: list[str]
    discovery_sizing_note: str


class TargetRecommendationResponse(BaseModel):
    """Response from recommend_azure_target."""

    ok: bool
    data: TargetRecommendation | None = None
    error: ToolError | None = None


class InventorySummary(BaseModel):
    """Executive portfolio summary backed by discovery sizing and shared inference."""

    report: DiscoveryReport
    executive_summary: str
    inference_provider: str | None = None
    inference_model: str | None = None


class InventorySummaryResponse(BaseModel):
    """Response from summarize_inventory."""

    ok: bool
    data: InventorySummary | None = None
    error: ToolError | None = None


class RoiEstimate(BaseModel):
    """ROI heuristic surfaced from the discovery report summary."""

    total_items: int
    total_indicative_monthly_cost_usd: float
    estimated_monthly_pp_savings_usd: float
    estimated_total_migration_cost_usd: float
    estimated_payback_months: float | None
    interpretation: Literal["positive-payback", "no-positive-payback"]


class RoiEstimateResponse(BaseModel):
    """Response from estimate_roi."""

    ok: bool
    data: RoiEstimate | None = None
    error: ToolError | None = None
