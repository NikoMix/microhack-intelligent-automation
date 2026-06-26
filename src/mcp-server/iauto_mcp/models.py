"""Typed input/output models shared by the intelligent-automation MCP tools.

Using `pydantic <https://docs.pydantic.dev>`_ models for tool inputs and outputs gives the
MCP server rich JSON schemas (so MCP clients can validate calls and render structured
results) and keeps the tool logic strongly typed for ``mypy --strict``.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class EstateInventory(BaseModel):
    """A coarse Power Platform estate inventory used for discovery & sizing.

    All counts default to zero so a caller can describe a partial estate. The values are
    *planning inputs*, not billing facts -- see :class:`SizingEstimate.assumptions`.
    """

    power_automate_flows: int = Field(
        default=0, ge=0, description="Number of Power Automate cloud flows in scope."
    )
    power_apps: int = Field(
        default=0, ge=0, description="Number of Power Apps (canvas or model-driven)."
    )
    dataverse_tables: int = Field(
        default=0, ge=0, description="Number of custom Dataverse tables to migrate."
    )
    premium_connectors: int = Field(
        default=0, ge=0, description="Distinct premium/custom connectors in use."
    )
    monthly_runs: int = Field(
        default=0, ge=0, description="Total monthly flow runs (executions) across the estate."
    )
    avg_run_seconds: float = Field(
        default=5.0, ge=0, description="Average wall-clock duration of a single flow run."
    )
    data_gb: float = Field(
        default=0.0, ge=0, description="Approximate data volume to migrate, in gigabytes."
    )


class SizingEstimate(BaseModel):
    """A deterministic, provider-free discovery & sizing estimate."""

    t_shirt_size: str = Field(description="Relative size band: S, M, L, or XL.")
    complexity_score: float = Field(description="Weighted complexity score (higher = harder).")
    monthly_action_executions: int = Field(
        description="Estimated monthly action executions on the Azure target."
    )
    monthly_compute_hours: float = Field(
        description="Estimated monthly compute hours implied by run count and duration."
    )
    effort_person_days: int = Field(description="Indicative migration effort in person-days.")
    recommended_targets: dict[str, str] = Field(
        description="Power Platform component -> recommended Azure landing service."
    )
    indicative_monthly_cost_band_usd: str = Field(
        description="Very rough monthly run-cost band on Azure (planning only)."
    )
    assumptions: list[str] = Field(description="Assumptions and caveats behind the estimate.")


class SizingResult(BaseModel):
    """A sizing estimate plus an optional natural-language narrative."""

    estimate: SizingEstimate
    narrative: str | None = Field(
        default=None, description="Optional AI-authored explanation of the estimate."
    )
    provider: str | None = Field(
        default=None, description="Inference provider that produced the narrative, if any."
    )
    model: str | None = Field(
        default=None, description="Model/deployment that produced the narrative, if any."
    )


class InferenceToolResult(BaseModel):
    """Normalised result for a text-generating tool, with provider attribution."""

    text: str = Field(description="The generated text.")
    provider: str = Field(description="Active inference provider (github|azure_openai|foundry).")
    model: str = Field(description="Model or deployment id that produced the text.")
    prompt_tokens: int | None = Field(default=None, description="Prompt tokens, if reported.")
    completion_tokens: int | None = Field(
        default=None, description="Completion tokens, if reported."
    )


class Passage(BaseModel):
    """A single retrieved context passage for grounded RAG answering."""

    text: str = Field(description="The passage text to ground the answer on.")
    source: str | None = Field(default=None, description="Optional citation/source label.")


class GroundedAnswer(BaseModel):
    """A RAG answer that is constrained to the supplied passages."""

    answer: str = Field(description="The grounded answer, or an explicit 'I don't know'.")
    passages_considered: int = Field(description="How many passages were supplied as context.")
    provider: str = Field(description="Active inference provider.")
    model: str = Field(description="Model or deployment id that produced the answer.")
