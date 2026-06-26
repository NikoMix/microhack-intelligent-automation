---
name: azure-landing-pattern
description: Choose an Azure landing pattern for Power Platform automations using the capstone MCP recommendations.
---

# Azure Landing Pattern

Use this skill when a learner asks which Azure service pattern should replace or augment a Power Platform automation.

## Decision workflow

1. Identify the automation type and constraints: UI dependency, connector count, run rate, data sensitivity, and on-premises coupling.
2. Call `iauto-migration/recommend_azure_target` for the default landing pattern.
3. If full sizing is needed, call `iauto-migration/assess_migration`.
4. Explain the recommended target in terms of Labs 3–4 implementation patterns:
   - Cloud flows → Azure Logic Apps Standard
   - Desktop/unattended RPA → Azure Functions or Container Apps Jobs, retaining hosted machines only for UI steps
   - AI Builder document processing → Azure AI Document Intelligence + Azure Functions
   - Copilot Studio → Azure AI Foundry agent + Azure AI Search
   - Predictive AI Builder scenarios → Azure ML or fit-for-purpose Azure AI services
5. Include security defaults: managed identity, Key Vault, private endpoints for medium/high sensitivity, diagnostic logging, and hybrid connectivity when on-premises dependencies exist.

## Output format

Return:

- Recommended Azure target
- Migration pattern
- Reference architecture identifier
- Sizing or effort caveat
- Security and operational notes
- Next implementation step for the learner
