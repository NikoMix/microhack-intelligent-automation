"""Render a discovery report as Markdown or JSON."""

from __future__ import annotations

from iauto_discovery.models import DiscoveryReport


def to_json(report: DiscoveryReport, *, indent: int = 2) -> str:
    """Serialize the report to JSON."""
    return report.model_dump_json(indent=indent)


def _summary_block(report: DiscoveryReport) -> list[str]:
    s = report.summary
    payback = (
        f"{s.estimated_payback_months} months"
        if s.estimated_payback_months is not None
        else "n/a (no net monthly saving)"
    )
    lines = [
        "## Portfolio summary",
        "",
        f"- **Automations assessed:** {s.total_items}",
        f"- **Indicative Azure run cost:** ${s.total_indicative_monthly_cost_usd:,.2f} / month",
        f"- **Power Platform premium avoided:** ${s.estimated_monthly_pp_savings_usd:,.2f} / month",
        f"- **One-off migration cost (indicative):** ${s.estimated_total_migration_cost_usd:,.2f}",
        f"- **Estimated payback:** {payback}",
        "",
        "### Azure targets",
        "",
    ]
    lines += [f"- {target}: {count}" for target, count in sorted(s.by_target.items())]
    lines += ["", "### Migration effort (t-shirt)", ""]
    lines += [f"- {size}: {count}" for size, count in sorted(s.by_effort.items())]
    return lines


def _assessment_table(report: DiscoveryReport) -> list[str]:
    header = "| Automation | Type | Azure target | Pattern ref | Tier | Effort | $/mo |"
    divider = "|---|---|---|---|---|---|---|"
    rows = [header, divider]
    for a in report.assessments:
        ref = a.notes[0] if a.notes else ""
        rows.append(
            f"| {a.item.name} | {a.item.automation_type.value} | {a.azure_target} | "
            f"{ref} | {a.sizing_tier.value} | {a.effort.value} | "
            f"${a.indicative_monthly_cost_usd:,.2f} |"
        )
    return rows


def to_markdown(report: DiscoveryReport) -> str:
    """Render a trainer-friendly Markdown report."""
    lines = ["# Discovery & sizing report", ""]
    lines += _summary_block(report)
    lines += ["", "## Per-automation recommendations", ""]
    lines += _assessment_table(report)

    if report.narrative:
        lines += ["", "## Executive narrative", "", report.narrative]

    lines += [
        "",
        "> 📋 **Evidence awareness:** In the specialization you would attach this report "
        "(or its source inventory) as discovery & sizing evidence (B.1.2). We generate it "
        "here; capturing it as an artifact is the only extra step an assessor expects.",
        "",
        "> ⚠️ Cost figures are **indicative bands** for teaching. Refine them with the "
        "Azure pricing tooling against the real target SKUs before quoting a customer.",
    ]
    return "\n".join(lines) + "\n"
