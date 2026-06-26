# Copilot instructions — Module B Intelligent Automation TTT Lab

This repository is a **1-day, classroom-led, hands-on Train-the-Trainer course**:
*From Power Platform to Azure — Intelligent Automation with GitHub Agents, Skills & MCP*.
It covers the buildable **Module B** requirements of the Intelligent Automation
specialization, with an **Azure-first** ("migrate Power Platform → Azure") narrative.

When working anywhere in this repo, follow these rules.

## Architecture & conventions

- **Polyglot:** Python for AI/agents/MCP (`src/inference/python`, `src/foundry-agent`,
  `src/mcp-server`), .NET for integration/Functions (`src/inference/dotnet`,
  `src/document-processing`, `src/hybrid-integration`). Match the language already in a
  folder; don't mix.
- **Modular inference everywhere.** Any AI capability MUST run on all three providers —
  **GitHub Models** (free, default), **Azure OpenAI**, **Azure AI Foundry** — selected by
  configuration only, never code. Reuse the shared inference layer:
  - Python: `iauto-inference` (`InferenceClient.from_env()`).
  - .NET: `IAuto.Inference` (`ChatClientFactory.CreateFromEnvironment()` → `IChatClient`).
  - **Do not** hard-code a provider or call `openai`/`AzureOpenAIClient` directly in feature
    code. If image generation is ever required, note that GitHub Models is exempt for that
    capability only.
- **Shared env-var contract** (identical in both languages): `INFERENCE_PROVIDER`
  (`github`|`azure_openai`|`foundry`); GitHub: `GITHUB_TOKEN`, `GITHUB_MODELS_ENDPOINT`,
  `GITHUB_MODELS_MODEL`; Azure OpenAI: `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_API_KEY`
  (optional → Entra), `AZURE_OPENAI_DEPLOYMENT`; Foundry: `AZURE_AI_FOUNDRY_ENDPOINT`,
  `AZURE_AI_FOUNDRY_MODEL`, `AZURE_AI_FOUNDRY_API_KEY` (optional → Entra); plus
  `INFERENCE_TIMEOUT`, `INFERENCE_MAX_RETRIES`.
- **Auth:** prefer **Entra ID / `DefaultAzureCredential`** over keys for Azure. Keys are a
  fallback for class delivery only. Never commit secrets; use `.env` (gitignored) +
  `.env.example`.
- **Agents/MCP:** prefer **Microsoft Agent Framework** (`agent-framework` for Python,
  `Microsoft.Agents.AI` for .NET) layered on `IChatClient`. It's public preview — verify
  against current docs/samples before relying on an API.

## Cost & licensing

- Default to **free / consumption** tiers (GitHub Models, Azure Functions Consumption,
  Logic Apps Standard dev, AI Search free/basic). Each lab notes a paid-tier upgrade path.
- **License-free dependencies only** (MIT / Apache-2.0 / Microsoft OSS). If no free library
  exists, build the capability instead of taking a paid/vendor-licensed one.

## Quality bar (non-negotiable)

- **Python:** `ruff` (lint+format), `mypy --strict`, `bandit` (security). All green.
- **.NET:** Roslyn analyzers + `EnforceCodeStyleInBuild`, `TreatWarningsAsErrors`, XML docs,
  `dotnet format --verify-no-changes`. All green.
- **Tests** for every component (pytest / xUnit). Keep them fast and provider-free (fakes).
- **Dependencies:** keep at the **latest** stable compatible versions; **zero known
  vulnerabilities** before finalizing (pip-audit / `dotnet list package --vulnerable` /
  `npm audit` / CodeQL / NuGetAudit). Document any pinned exception.
- **Telemetry:** prefer OpenTelemetry → Azure Monitor / Application Insights for runtime;
  rely on analyzers for code-smell telemetry.

## Course-specific rules

- **Evidence awareness, not evidence busywork.** The specialization requires evidence
  artifacts; this course teaches the *buildable* tasks. Where a step would normally produce
  evidence, add a short `> 📋 Evidence awareness:` callout explaining what an assessor
  would capture — then move on. Do **not** build evidence-collection tooling.
- **Lab structure:** each `labs/lab-N-*/README.md` is a self-contained guide with:
  objectives → Module B mapping → prerequisites → numbered steps → validation →
  paid-tier upgrade notes → 📋 evidence-awareness callout → trainer notes.
- **Train-the-Trainer:** keep `docs/` facilitator-ready (timings, talking points, common
  pitfalls, reset steps). Solutions live on the `solutions` branch.

## Module B → labs (buildable only)

- B.1.1 Platform delivery capability → Labs 3, 4, 5, 6 (Azure reference architectures).
- B.1.2 Discovery & sizing → Lab 1 (`tools/discovery`).
- B.3.2 ALM for Power Platform/Azure → Lab 6 (Bicep + GitHub Actions + environments).
- B.2.x / B.3.1 / B.4.x → evidence-awareness callouts only (not buildable labs).

## Workflow

- Track work via **GitHub Issues** (an epic + per-lab issues). Reference the issue in PRs.
- Standardize local + CI Python on **3.12** (via `uv`); .NET on **net10.0**.
- Use `gh` CLI for GitHub operations. Conventional commits; include the Copilot
  `Co-authored-by` trailer.
