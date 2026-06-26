"""FastMCP server exposing Azure migration tools for the capstone lab."""

from __future__ import annotations

import argparse
import logging
import sys
from collections.abc import Sequence
from typing import Literal, NoReturn, cast

from iauto_discovery.engine import assess_item, build_report
from iauto_discovery.models import (
    AutomationType,
    Complexity,
    InventoryItem,
    RoiAssumptions,
    Sensitivity,
)
from iauto_discovery.rules import target_for
from iauto_inference import InferenceClient
from mcp.server.fastmcp import FastMCP
from pydantic import ValidationError

from iauto_mcp.models import (
    AssessmentResponse,
    AutomationInventoryItem,
    InventorySummary,
    InventorySummaryResponse,
    RoiEstimate,
    RoiEstimateResponse,
    TargetRecommendation,
    TargetRecommendationResponse,
    ToolError,
)

LOGGER = logging.getLogger("iauto_mcp")
Transport = Literal["stdio", "streamable-http"]

mcp = FastMCP("iauto-migration-advisor")

_SUMMARY_SYSTEM_PROMPT = (
    "You are an Azure migration advisor for a one-day Train-the-Trainer capstone. "
    "Summarize the discovery report for executives in 5-7 concise bullets. Include "
    "recommended migration waves, target Azure patterns, headline effort/cost/ROI, "
    "and security risks. Cite the deterministic discovery sizing and avoid unsupported claims."
)


def _configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
        stream=sys.stderr,
    )


def _tool_error(code: str, message: str, details: list[str] | None = None) -> ToolError:
    return ToolError(code=code, message=message, details=details or [])


def _validation_details(exc: ValidationError) -> list[str]:
    return [
        f"{'.'.join(str(part) for part in error['loc'])}: {error['msg']}" for error in exc.errors()
    ]


def _unexpected_error(exc: Exception) -> ToolError:
    LOGGER.exception("MCP tool failed")
    return _tool_error(type(exc).__name__, "Tool execution failed.", [str(exc)])


def _summary_prompt(report_json: str) -> list[dict[str, str]]:
    return [
        {"role": "system", "content": _SUMMARY_SYSTEM_PROMPT},
        {"role": "user", "content": f"Discovery report JSON:\n{report_json}"},
    ]


def _automation_type(value: AutomationType | str) -> AutomationType:
    return value if isinstance(value, AutomationType) else AutomationType(value)


def _complexity(value: Complexity | str) -> Complexity:
    return value if isinstance(value, Complexity) else Complexity(value)


def _sensitivity(value: Sensitivity | str) -> Sensitivity:
    return value if isinstance(value, Sensitivity) else Sensitivity(value)


@mcp.tool()
async def assess_migration(
    item: AutomationInventoryItem,
    assumptions: RoiAssumptions | None = None,
) -> AssessmentResponse:
    """Assess one Power Platform automation and return Azure target, sizing, and effort."""
    try:
        assessment = assess_item(item.to_discovery_item(), assumptions)
        return AssessmentResponse(ok=True, data=assessment)
    except ValidationError as exc:
        return AssessmentResponse(
            ok=False,
            error=_tool_error(
                "validation_error",
                "Invalid migration assessment input.",
                _validation_details(exc),
            ),
        )
    except Exception as exc:
        return AssessmentResponse(ok=False, error=_unexpected_error(exc))


@mcp.tool()
async def recommend_azure_target(
    automation_type: AutomationType | str,
    complexity: Complexity | str = Complexity.MEDIUM,
    sensitivity: Sensitivity | str = Sensitivity.LOW,
    connectors: int = 0,
    on_prem_dependency: bool = False,
) -> TargetRecommendationResponse:
    """Recommend the Azure landing pattern and reference architecture for an automation type."""
    try:
        normalized_type = _automation_type(automation_type)
        item = InventoryItem(
            name=f"{normalized_type.value}-candidate",
            automation_type=normalized_type,
            connectors=connectors,
            complexity=_complexity(complexity),
            data_sensitivity=_sensitivity(sensitivity),
            on_prem_dependency=on_prem_dependency,
        )
        target, pattern, reference_architecture = target_for(item)
        assessment = assess_item(item)
        recommendation = TargetRecommendation(
            automation_type=normalized_type,
            azure_target=target,
            migration_pattern=pattern,
            reference_architecture=reference_architecture,
            default_security_recommendations=assessment.security_recommendations,
            discovery_sizing_note=(
                f"Default discovery heuristic rates this as {assessment.effort.value} effort "
                f"and {assessment.sizing_tier.value} size before run-rate is supplied."
            ),
        )
        return TargetRecommendationResponse(ok=True, data=recommendation)
    except ValidationError as exc:
        return TargetRecommendationResponse(
            ok=False,
            error=_tool_error(
                "validation_error",
                "Invalid target recommendation input.",
                _validation_details(exc),
            ),
        )
    except ValueError as exc:
        return TargetRecommendationResponse(
            ok=False,
            error=_tool_error(
                "validation_error",
                "Invalid target recommendation input.",
                [str(exc)],
            ),
        )
    except Exception as exc:
        return TargetRecommendationResponse(ok=False, error=_unexpected_error(exc))


@mcp.tool()
async def summarize_inventory(
    items: list[AutomationInventoryItem],
    assumptions: RoiAssumptions | None = None,
    model: str | None = None,
) -> InventorySummaryResponse:
    """Summarize an automation inventory with discovery sizing plus provider-swappable inference."""
    try:
        if not items:
            return InventorySummaryResponse(
                ok=False,
                error=_tool_error("validation_error", "Inventory must contain at least one item."),
            )
        report = build_report([item.to_discovery_item() for item in items], assumptions)
        client = InferenceClient.from_env()
        result = await client.acomplete(
            _summary_prompt(report.model_dump_json(indent=2)),
            model=model,
            temperature=0.2,
            max_tokens=650,
        )
        summary = InventorySummary(
            report=report,
            executive_summary=result.text.strip(),
            inference_provider=result.provider,
            inference_model=result.model,
        )
        return InventorySummaryResponse(ok=True, data=summary)
    except ValidationError as exc:
        return InventorySummaryResponse(
            ok=False,
            error=_tool_error(
                "validation_error",
                "Invalid inventory summary input.",
                _validation_details(exc),
            ),
        )
    except Exception as exc:
        return InventorySummaryResponse(ok=False, error=_unexpected_error(exc))


@mcp.tool()
async def estimate_roi(
    items: list[AutomationInventoryItem],
    assumptions: RoiAssumptions | None = None,
) -> RoiEstimateResponse:
    """Estimate portfolio ROI using the shared discovery engine heuristic."""
    try:
        if not items:
            return RoiEstimateResponse(
                ok=False,
                error=_tool_error("validation_error", "Inventory must contain at least one item."),
            )
        report = build_report([item.to_discovery_item() for item in items], assumptions)
        summary = report.summary
        estimate = RoiEstimate(
            total_items=summary.total_items,
            total_indicative_monthly_cost_usd=summary.total_indicative_monthly_cost_usd,
            estimated_monthly_pp_savings_usd=summary.estimated_monthly_pp_savings_usd,
            estimated_total_migration_cost_usd=summary.estimated_total_migration_cost_usd,
            estimated_payback_months=summary.estimated_payback_months,
            interpretation=(
                "positive-payback"
                if summary.estimated_payback_months is not None
                else "no-positive-payback"
            ),
        )
        return RoiEstimateResponse(ok=True, data=estimate)
    except ValidationError as exc:
        return RoiEstimateResponse(
            ok=False,
            error=_tool_error(
                "validation_error",
                "Invalid ROI estimate input.",
                _validation_details(exc),
            ),
        )
    except Exception as exc:
        return RoiEstimateResponse(ok=False, error=_unexpected_error(exc))


def _parse_args(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the intelligent automation MCP server.")
    parser.add_argument(
        "--transport",
        choices=("stdio", "streamable-http"),
        default="stdio",
        help="MCP transport. stdio is the default for Copilot/CLI integrations.",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> NoReturn:
    """Console entry point."""
    _configure_logging()
    args = _parse_args(argv)
    transport = cast("Transport", args.transport)
    LOGGER.info("Starting iauto MCP server with %s transport", transport)
    mcp.run(transport=transport)
    raise SystemExit(0)


if __name__ == "__main__":
    main()
