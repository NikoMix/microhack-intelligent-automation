"""Assessment engine: turn an inventory into sized, costed migration recommendations."""

from __future__ import annotations

from collections import Counter

from iauto_discovery import rules
from iauto_discovery.models import (
    DiscoveryReport,
    EffortTShirt,
    InventoryItem,
    ItemAssessment,
    PortfolioSummary,
    RoiAssumptions,
    SizingTier,
)


def _monthly_minutes(item: InventoryItem, assumptions: RoiAssumptions) -> float:
    return item.runs_per_day * item.avg_minutes * assumptions.working_days_per_month


def _cost_for_tier(tier: SizingTier, assumptions: RoiAssumptions) -> float:
    return {
        SizingTier.SMALL: assumptions.azure_cost_small,
        SizingTier.MEDIUM: assumptions.azure_cost_medium,
        SizingTier.LARGE: assumptions.azure_cost_large,
    }[tier]


def _effort_cost(effort: EffortTShirt, assumptions: RoiAssumptions) -> float:
    return {
        EffortTShirt.S: assumptions.effort_cost_s,
        EffortTShirt.M: assumptions.effort_cost_m,
        EffortTShirt.L: assumptions.effort_cost_l,
        EffortTShirt.XL: assumptions.effort_cost_xl,
    }[effort]


def assess_item(item: InventoryItem, assumptions: RoiAssumptions | None = None) -> ItemAssessment:
    """Produce the full migration recommendation for a single automation."""
    assumptions = assumptions or RoiAssumptions()

    monthly_minutes = _monthly_minutes(item, assumptions)
    tier = rules.sizing_tier(monthly_minutes)
    target, pattern, ref_arch = rules.target_for(item)
    effort = rules.effort_for(item)

    notes = [ref_arch]
    if monthly_minutes == 0:
        notes.append("No run-rate provided; sizing defaulted to the smallest tier.")
    if item.premium_licensed:
        notes.append("Currently consumes Power Platform premium licensing (savings candidate).")

    return ItemAssessment(
        item=item,
        azure_target=target,
        migration_pattern=pattern,
        sizing_tier=tier,
        monthly_execution_minutes=round(monthly_minutes, 1),
        effort=effort,
        indicative_monthly_cost_usd=round(_cost_for_tier(tier, assumptions), 2),
        security_recommendations=rules.security_recommendations(item),
        notes=notes,
    )


def build_report(
    items: list[InventoryItem],
    assumptions: RoiAssumptions | None = None,
) -> DiscoveryReport:
    """Assess every item and aggregate a portfolio summary with an ROI heuristic."""
    assumptions = assumptions or RoiAssumptions()
    assessments = [assess_item(item, assumptions) for item in items]

    by_target = Counter(a.azure_target for a in assessments)
    by_effort = Counter(a.effort.value for a in assessments)

    total_monthly_cost = round(sum(a.indicative_monthly_cost_usd for a in assessments), 2)
    gross_pp_savings = round(
        sum(assumptions.pp_premium_monthly for a in assessments if a.item.premium_licensed), 2
    )
    total_migration_cost = round(
        sum(_effort_cost(a.effort, assumptions) for a in assessments), 2
    )

    net_monthly_savings = gross_pp_savings - total_monthly_cost
    payback_months: float | None = (
        round(total_migration_cost / net_monthly_savings, 1) if net_monthly_savings > 0 else None
    )

    summary = PortfolioSummary(
        total_items=len(assessments),
        by_target=dict(by_target),
        by_effort=dict(by_effort),
        total_indicative_monthly_cost_usd=total_monthly_cost,
        estimated_monthly_pp_savings_usd=gross_pp_savings,
        estimated_total_migration_cost_usd=total_migration_cost,
        estimated_payback_months=payback_months,
    )

    return DiscoveryReport(assessments=assessments, summary=summary)
