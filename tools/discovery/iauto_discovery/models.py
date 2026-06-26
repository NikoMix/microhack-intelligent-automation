"""Domain models for discovery, sizing, and migration decisioning (Module B.1.2).

All inputs and outputs are strongly typed with pydantic so the tool is testable and
the contract is explicit for the lab. Cost figures are *indicative bands*, not quotes —
the lab shows how to refine them with the Azure pricing tooling.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class AutomationType(str, Enum):
    """The Power Platform automation kinds we know how to size and migrate."""

    ATTENDED_RPA = "attended_rpa"
    UNATTENDED_RPA = "unattended_rpa"
    DESKTOP_FLOW = "desktop_flow"
    CLOUD_FLOW = "cloud_flow"
    COPILOT_STUDIO = "copilot_studio"
    AI_BUILDER_DOC = "ai_builder_doc"
    AI_BUILDER_PREDICT = "ai_builder_predict"


class Complexity(str, Enum):
    """Relative build/migration complexity of an automation."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Sensitivity(str, Enum):
    """Data sensitivity, drives security + networking recommendations."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class SizingTier(str, Enum):
    """Coarse sizing tier derived from monthly execution minutes."""

    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"


class EffortTShirt(str, Enum):
    """T-shirt migration effort estimate."""

    S = "S"
    M = "M"
    L = "L"
    XL = "XL"


class InventoryItem(BaseModel):
    """One automation from the customer's Power Platform estate."""

    model_config = {"extra": "forbid"}

    name: str
    automation_type: AutomationType
    runs_per_day: float = Field(ge=0, default=0)
    avg_minutes: float = Field(ge=0, default=0)
    connectors: int = Field(ge=0, default=0)
    complexity: Complexity = Complexity.MEDIUM
    data_sensitivity: Sensitivity = Sensitivity.LOW
    on_prem_dependency: bool = False
    premium_licensed: bool = False


class RoiAssumptions(BaseModel):
    """Tunable economic assumptions for the ROI heuristic.

    Defaults are conservative, documented placeholders — override them with the
    customer's real rates (the lab walks through this).
    """

    model_config = {"extra": "forbid"}

    working_days_per_month: float = Field(gt=0, default=21)
    # Indicative monthly Azure consumption cost per sizing tier (USD).
    azure_cost_small: float = Field(ge=0, default=15)
    azure_cost_medium: float = Field(ge=0, default=75)
    azure_cost_large: float = Field(ge=0, default=300)
    # Indicative monthly Power Platform premium cost avoided per premium-licensed item.
    pp_premium_monthly: float = Field(ge=0, default=15)
    # Indicative migration effort cost (USD) per t-shirt size (one-off).
    effort_cost_s: float = Field(ge=0, default=2000)
    effort_cost_m: float = Field(ge=0, default=6000)
    effort_cost_l: float = Field(ge=0, default=15000)
    effort_cost_xl: float = Field(ge=0, default=35000)


class ItemAssessment(BaseModel):
    """The full recommendation for a single automation."""

    item: InventoryItem
    azure_target: str
    migration_pattern: str
    sizing_tier: SizingTier
    monthly_execution_minutes: float
    effort: EffortTShirt
    indicative_monthly_cost_usd: float
    security_recommendations: list[str]
    notes: list[str]


class PortfolioSummary(BaseModel):
    """Aggregate portfolio view across all assessed items."""

    total_items: int
    by_target: dict[str, int]
    by_effort: dict[str, int]
    total_indicative_monthly_cost_usd: float
    estimated_monthly_pp_savings_usd: float
    estimated_total_migration_cost_usd: float
    estimated_payback_months: float | None


class DiscoveryReport(BaseModel):
    """The complete discovery + sizing output."""

    assessments: list[ItemAssessment]
    summary: PortfolioSummary
    narrative: str | None = None
