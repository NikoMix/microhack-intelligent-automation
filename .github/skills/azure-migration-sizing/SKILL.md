---
name: azure-migration-sizing
description: Size and score a Power Platform automation inventory for Azure migration using the Lab 5 MCP server and shared discovery heuristics.
---

# Azure Migration Sizing

Use this skill when a learner asks how to assess Power Platform automations for Azure migration, estimate effort, or prepare a migration wave plan.

## Inputs to collect

For each inventory item, collect:

- `name`
- `type` / `automation_type`: `attended_rpa`, `unattended_rpa`, `desktop_flow`, `cloud_flow`, `copilot_studio`, `ai_builder_doc`, or `ai_builder_predict`
- `complexity`: `low`, `medium`, or `high`
- `connectors`: connector count or connector names
- `runs_per_day` and `avg_minutes`
- `sensitivity`: `low`, `medium`, or `high`
- `on_prem_dependency`
- `premium_licensed`

## Procedure

1. Start the MCP server from `src\mcp-server` with `uv run iauto-mcp`.
2. Use the `iauto-migration/assess_migration` tool for each item.
3. Use `iauto-migration/estimate_roi` for the portfolio.
4. Use `iauto-migration/summarize_inventory` when an executive summary is needed; provider choice comes from `INFERENCE_PROVIDER`.
5. Report the deterministic discovery outputs: Azure target, migration pattern, sizing tier, effort T-shirt, indicative monthly Azure cost, migration cost, payback, and security notes.

## Trainer guidance

- Explain that Lab 5 reuses the Lab 1 discovery engine instead of duplicating sizing logic.
- Treat cost figures as indicative bands for learning. For customer delivery, refine with Azure Pricing Calculator or Azure pricing APIs.
- If a tool returns `ok: false`, fix the inventory data and rerun rather than inventing estimates.
