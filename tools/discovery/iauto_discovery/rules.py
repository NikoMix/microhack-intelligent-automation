"""Deterministic migration rules: Power Platform automation → Azure target + pattern.

These are the buildable, offline heuristics that drive Module B.1.2 sizing and
migration decisioning. They are intentionally transparent (no hidden ML) so trainers
can explain every recommendation.
"""

from __future__ import annotations

from iauto_discovery.models import (
    AutomationType,
    Complexity,
    EffortTShirt,
    InventoryItem,
    Sensitivity,
    SizingTier,
)

# Azure target + migration narrative per automation type. Azure-first, with the
# "migrate Power Platform → Azure" story baked in.
_TARGETS: dict[AutomationType, tuple[str, str]] = {
    AutomationType.ATTENDED_RPA: (
        "Azure Logic Apps Standard + Functions (UI steps stay on PAD/hosted machines)",
        "Lift orchestration to Logic Apps Standard; keep attended UI automation on Power "
        "Automate Desktop hosted machines; call Azure Functions for custom logic.",
    ),
    AutomationType.UNATTENDED_RPA: (
        "Azure Container Apps Jobs / Functions (+ hosted machine group for UI)",
        "Re-platform headless logic to Container Apps Jobs or Functions; retain a hosted "
        "machine group only where genuine UI automation remains.",
    ),
    AutomationType.DESKTOP_FLOW: (
        "Azure Functions (+ Power Automate Desktop hosted machines for UI)",
        "Convert API/data steps to Functions; keep desktop UI steps on hosted machines.",
    ),
    AutomationType.CLOUD_FLOW: (
        "Azure Logic Apps Standard",
        "Cloud flows map closely to Logic Apps Standard workflows; migrate connectors and "
        "triggers, parameterize per environment.",
    ),
    AutomationType.COPILOT_STUDIO: (
        "Azure AI Foundry agent + Azure AI Search (RAG)",
        "Rebuild the bot as an Azure AI Foundry agent grounded with RAG over Azure AI "
        "Search; expose tools via the modular inference layer.",
    ),
    AutomationType.AI_BUILDER_DOC: (
        "Azure AI Document Intelligence + Azure Functions",
        "Replace AI Builder document processing with Azure AI Document Intelligence; "
        "orchestrate with Functions and human-in-the-loop.",
    ),
    AutomationType.AI_BUILDER_PREDICT: (
        "Azure Machine Learning / Azure AI services",
        "Move custom prediction models to Azure ML or a fit-for-purpose Azure AI service.",
    ),
}

# Module B reference-architecture pattern id, for traceability in the lab.
_REF_ARCH: dict[AutomationType, str] = {
    AutomationType.ATTENDED_RPA: "Ref-Arch 1: Attended RPA",
    AutomationType.UNATTENDED_RPA: "Ref-Arch 2: Unattended RPA",
    AutomationType.DESKTOP_FLOW: "Ref-Arch 2: Unattended RPA",
    AutomationType.CLOUD_FLOW: "Ref-Arch 5: Hybrid integration",
    AutomationType.COPILOT_STUDIO: "Ref-Arch 3: Copilot Studio + RAG",
    AutomationType.AI_BUILDER_DOC: "Ref-Arch 4: Document processing",
    AutomationType.AI_BUILDER_PREDICT: "Ref-Arch 6: Event-driven AI",
}


def target_for(item: InventoryItem) -> tuple[str, str, str]:
    """Return ``(azure_target, migration_pattern, reference_architecture)``."""
    target, pattern = _TARGETS[item.automation_type]
    return target, pattern, _REF_ARCH[item.automation_type]


def sizing_tier(monthly_minutes: float) -> SizingTier:
    """Map monthly execution minutes to a coarse sizing tier."""
    if monthly_minutes < _SMALL_TIER_CEILING:
        return SizingTier.SMALL
    if monthly_minutes < _MEDIUM_TIER_CEILING:
        return SizingTier.MEDIUM
    return SizingTier.LARGE


# Sizing thresholds (monthly execution minutes).
_SMALL_TIER_CEILING = 2_000
_MEDIUM_TIER_CEILING = 20_000

# Effort scoring: base by complexity, escalated by connectors / on-prem coupling.
_COMPLEXITY_SCORE: dict[Complexity, int] = {
    Complexity.LOW: 1,
    Complexity.MEDIUM: 2,
    Complexity.HIGH: 3,
}

# Some targets are inherently heavier lifts than a like-for-like flow migration.
_TYPE_EFFORT_BUMP: dict[AutomationType, int] = {
    AutomationType.COPILOT_STUDIO: 1,
    AutomationType.AI_BUILDER_PREDICT: 1,
    AutomationType.UNATTENDED_RPA: 1,
}

# Effort escalators and t-shirt score ceilings.
_CONNECTOR_HEAVY = 5
_EFFORT_S_MAX = 1
_EFFORT_M_MAX = 3
_EFFORT_L_MAX = 5


def effort_for(item: InventoryItem) -> EffortTShirt:
    """Estimate a t-shirt migration effort from complexity, connectors, coupling."""
    score = _COMPLEXITY_SCORE[item.complexity]
    score += _TYPE_EFFORT_BUMP.get(item.automation_type, 0)
    if item.connectors >= _CONNECTOR_HEAVY:
        score += 1
    if item.on_prem_dependency:
        score += 1
    if item.data_sensitivity is Sensitivity.HIGH:
        score += 1

    if score <= _EFFORT_S_MAX:
        return EffortTShirt.S
    if score <= _EFFORT_M_MAX:
        return EffortTShirt.M
    if score <= _EFFORT_L_MAX:
        return EffortTShirt.L
    return EffortTShirt.XL


def security_recommendations(item: InventoryItem) -> list[str]:
    """Security + networking guidance driven by sensitivity and on-prem coupling."""
    recs: list[str] = [
        "Use Entra ID + managed identity (DefaultAzureCredential); avoid keys.",
        "Store any required secrets in Azure Key Vault.",
    ]
    if item.data_sensitivity in (Sensitivity.MEDIUM, Sensitivity.HIGH):
        recs.append("Enable Private Endpoints and disable public network access.")
        recs.append("Apply customer-managed keys + diagnostic logging to Log Analytics.")
    if item.data_sensitivity is Sensitivity.HIGH:
        recs.append("Add Microsoft Defender for Cloud coverage and data-loss controls.")
    if item.on_prem_dependency:
        recs.append(
            "Bridge on-prem via VNet integration + Logic Apps hybrid connections or an "
            "on-premises data gateway."
        )
    return recs
