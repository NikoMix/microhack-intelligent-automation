---
name: draft-azure-migration-plan
description: 'Draft a structured, buildable Power Platform → Azure migration plan with consistent sections and Azure Well-Architected guardrails, defaulting to free/consumption tiers. Pairs with the iauto-automation MCP server draft_migration_plan tool. WHEN: "migrate this flow to Azure", "Power Automate to Logic Apps", "Power Apps to App Service", "Dataverse to Azure SQL", "draft a migration plan", "modernization plan for this workload". DO NOT USE FOR: provisioning live infrastructure, writing IaC/Bicep/Terraform, or greenfield Azure design with no Power Platform source.'
license: MIT
metadata:
  author: Intelligent Automation TTT
  version: '1.0.0'
---

# Draft Azure Migration Plan

> Produce a **consistent, buildable** Power Platform → Azure migration plan. Default to
> **free / consumption** tiers and Azure Well-Architected best practices. Plans are decision
> artifacts, not deployments — never provision anything from this skill.

## Rules

1. **Always** emit the standard sections, in order (see [plan-template.md](references/plan-template.md)):
   Overview · Target architecture · Migration steps · Risks & mitigations · Validation · Rollback.
2. **Map sources to Azure landing services** explicitly:
   - Power Automate cloud flows → **Azure Logic Apps (Standard)** or **Azure Functions**
   - Power Apps → **Azure App Service / Static Web Apps** (+ **Azure Functions** for logic)
   - Dataverse tables → **Azure SQL Database** or **Azure Cosmos DB**
   - Premium / custom connectors → **Azure API Management** + Logic Apps connectors
   - AI Builder / Copilot → **Azure AI Foundry / Azure OpenAI** via the modular inference layer
3. **Keep AI provider-agnostic.** Any AI step must run on the shared inference layer (GitHub
   Models / Azure OpenAI / Azure AI Foundry by configuration). Pair with the
   `scaffold-modular-inference` skill when the plan adds an AI capability.
4. **Security & identity first.** Prefer **Entra ID** (`DefaultAzureCredential`), managed
   identities, and Key Vault. No secrets in plans or code.
5. **Be honest about cost & uncertainty.** Note that sizing/cost figures are planning estimates;
   point to the Azure pricing calculator and Power Platform admin analytics / CoE toolkit for
   real numbers.

## Steps

1. **Capture inputs:** workload description, source components, data volumes, SLAs, constraints,
   and the target provider/config.
2. **(Optional) Size first** with the `estimate_discovery_sizing` MCP tool to ground scope/effort.
3. **Draft** using the `draft_migration_plan` MCP tool *or* the [plan template](references/plan-template.md)
   if writing by hand — keep the section set identical either way.
4. **Review** against Well-Architected pillars (reliability, security, cost, operational
   excellence, performance) and trim to the free/consumption path unless told otherwise.
5. **Hand off** concrete next actions (e.g. scaffold IaC, set up CI/CD) to the relevant lab.

> 📋 Evidence awareness: an assessor would capture the migration plan artifact plus the inputs and
> sizing that justified it. Produce the plan; do not build evidence-collection tooling.

## Reference index

| Reference | When to load |
| --- | --- |
| [references/plan-template.md](references/plan-template.md) | Writing or reviewing a plan by hand |
