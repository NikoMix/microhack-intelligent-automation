# `iauto-discovery` — discovery, sizing & migration decisioning

> **Module B.1.2 lab artifact.** Turns a Power Platform automation inventory into
> Azure migration targets, sizing tiers, t-shirt effort, security guidance, and an ROI
> heuristic — fully **offline and deterministic** so every recommendation is explainable
> in the classroom. An optional LLM **executive narrative** runs on the shared modular
> inference layer (GitHub Models / Azure OpenAI / Azure AI Foundry).

## Why it exists

In Module B you must demonstrate **discovery & sizing** before recommending a platform.
This tool is the worked example: feed it a CSV/JSON inventory of the customer's flows,
desktop flows, Copilot Studio bots and AI Builder models, and it produces a report you
can hand to an architect — mapping each automation to an Azure-first reference
architecture with an indicative cost and payback.

## Install (uv, Python 3.12)

```bash
cd tools/discovery
uv venv --python 3.12
uv pip install -e ".[dev]"          # core + quality tooling
# optional: LLM narrative via the shared inference layer
uv pip install -e ".[dev,ai]"
```

## Use

```bash
# Markdown report to stdout
uv run iauto-discover samples/inventory.csv

# JSON for downstream tooling
uv run iauto-discover samples/inventory.csv --json --out report.json

# Override the economic assumptions and add an LLM narrative
uv run iauto-discover samples/inventory.csv \
    --assumptions my-rates.json --narrative --out report.md
```

### Inventory schema

| Column | Type | Notes |
|---|---|---|
| `name` | string | Automation display name |
| `automation_type` | enum | `attended_rpa`, `unattended_rpa`, `desktop_flow`, `cloud_flow`, `copilot_studio`, `ai_builder_doc`, `ai_builder_predict` |
| `runs_per_day` | number | Average executions per working day |
| `avg_minutes` | number | Average minutes per run |
| `connectors` | int | Distinct connectors used |
| `complexity` | enum | `low`, `medium`, `high` |
| `data_sensitivity` | enum | `low`, `medium`, `high` |
| `on_prem_dependency` | bool | Touches on-prem systems |
| `premium_licensed` | bool | Consumes Power Platform premium today |

Booleans accept `true/false`, `yes/no`, `1/0`. JSON may be a bare array or `{ "items": [...] }`.

### Override ROI assumptions

All economic inputs are documented placeholders — replace them with the customer's real
rates (`--assumptions rates.json`):

```json
{
  "working_days_per_month": 21,
  "azure_cost_small": 15, "azure_cost_medium": 75, "azure_cost_large": 300,
  "pp_premium_monthly": 15,
  "effort_cost_s": 2000, "effort_cost_m": 6000, "effort_cost_l": 15000, "effort_cost_xl": 35000
}
```

## How sizing & effort work

- **Sizing tier** from monthly execution minutes (`runs_per_day × avg_minutes ×
  working_days`): `<2,000` small · `<20,000` medium · else large.
- **Effort** scores complexity, then escalates for ≥5 connectors, on-prem coupling, high
  sensitivity, and heavier target types (Copilot Studio, custom prediction, unattended
  RPA) → S/M/L/XL.
- **Target** maps each automation type to an Azure-first reference architecture
  (Logic Apps Standard, Functions, Container Apps Jobs, AI Foundry + AI Search,
  Document Intelligence, Azure ML).

> ⚠️ Costs are **indicative teaching bands**, not quotes. The lab shows how to refine
> them with the Azure pricing tooling against real SKUs.

> 📋 **Evidence awareness:** the generated report (and its source inventory) is exactly
> the discovery & sizing artifact an assessor expects for B.1.2 — generating it is the
> work; saving it is the only extra step.

## Quality gates

```bash
uv run ruff check .
uv run mypy iauto_discovery
uv run bandit -c pyproject.toml -r iauto_discovery
uv run pytest
```

All four must pass clean; CI runs the same set.
