"""Optional LLM-generated executive narrative via the shared modular inference layer.

Offline by default. When ``--narrative`` is requested, this calls the same
``iauto-inference`` client used everywhere else, so the narrative runs on GitHub Models
(free), Azure OpenAI, or Azure AI Foundry by configuration only.
"""

from __future__ import annotations

from iauto_discovery.models import DiscoveryReport

_SYSTEM = (
    "You are a cloud migration advisor. Given a Power Platform → Azure discovery and "
    "sizing summary, write a concise executive narrative (max ~200 words): the migration "
    "story, suggested waves (quick wins first), key risks, and the headline ROI. Be "
    "specific and avoid hype."
)


def _prompt(report: DiscoveryReport) -> str:
    s = report.summary
    targets = "; ".join(f"{k}: {v}" for k, v in sorted(s.by_target.items()))
    efforts = "; ".join(f"{k}: {v}" for k, v in sorted(s.by_effort.items()))
    return (
        f"Automations: {s.total_items}. Azure targets -> {targets}. "
        f"Effort mix -> {efforts}. Indicative Azure cost "
        f"${s.total_indicative_monthly_cost_usd:,.2f}/mo; premium avoided "
        f"${s.estimated_monthly_pp_savings_usd:,.2f}/mo; migration cost "
        f"${s.estimated_total_migration_cost_usd:,.2f}; payback "
        f"{s.estimated_payback_months} months."
    )


def generate_narrative(report: DiscoveryReport) -> str:
    """Generate an executive narrative. Requires the ``ai`` extra + a configured provider."""
    try:
        from iauto_inference import InferenceClient  # noqa: PLC0415 (optional dependency)
    except ImportError as exc:  # pragma: no cover - exercised via CLI message
        msg = (
            "The 'ai' extra is required for --narrative. Install with "
            "`uv pip install -e .[ai]` and configure an inference provider."
        )
        raise RuntimeError(msg) from exc

    client = InferenceClient.from_env()
    messages = [
        {"role": "system", "content": _SYSTEM},
        {"role": "user", "content": _prompt(report)},
    ]
    return client.complete(messages, temperature=0.3, max_tokens=400).text.strip()
