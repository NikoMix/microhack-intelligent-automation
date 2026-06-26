# Lab 4 — Migrate a Copilot Studio Knowledge Agent to Azure AI Foundry RAG

In this lab you move a typical **Copilot Studio knowledge agent** pattern into an Azure-first architecture: **Microsoft Agent Framework** orchestrates the agent, **Azure AI Search** stores the migrated knowledge sources, **Azure AI Foundry / Azure OpenAI / GitHub Models** generate grounded answers, and **Application Insights** captures telemetry.

## What you build

- Azure AI Search index with sample HR/IT/procurement knowledge articles.
- Azure AI Services / Foundry account and Foundry project.
- Python 3.12 Agent Framework app with:
  - an Azure AI Search retrieval tool,
  - citations using document title + section,
  - `iauto_inference` provider-swappable summarization,
  - optional native `FoundryChatClient` runtime.

## Migration framing

| Copilot Studio concept | Azure-first replacement in this lab |
|---|---|
| Knowledge sources | Markdown docs ingested into Azure AI Search |
| Topics / generative orchestration | Microsoft Agent Framework instructions + retrieval tool |
| Copilot Studio answer grounding | RAG prompt with citations from Azure AI Search |
| Studio analytics | OpenTelemetry traces exported to Application Insights |
| Environment variables / connections | Managed identity + RBAC + `.env` for local dev |

Agent Framework replaces Copilot Studio's managed orchestration loop. Your Python code owns when to retrieve, summarize, call tools, and route generation.

> 📋 **Evidence awareness — Module B.1.1:** This lab is a lightweight reference architecture for “Power Platform + Azure delivery capability”: Copilot Studio knowledge agent → Azure AI Foundry agent + Azure AI Search RAG + managed identity + telemetry. Capture the deployed architecture diagram and a sample grounded answer as evidence.

## Prerequisites

- Azure subscription and rights to create a resource group deployment and role assignments.
- Azure CLI with Bicep CLI 0.44+ (`az bicep version`).
- Python 3.12 and `uv`.
- GitHub token for GitHub Models, or Azure OpenAI / Foundry model access.
- From repo root, stay inside `src\foundry-agent`, `infra\bicep\foundry-search`, and `labs\lab-4` for lab work.

## 1. Provision shared core and Foundry/Search

From repo root:

```powershell
az group create --name rg-iauto-lab4 --location swedencentral
az deployment group create `
  --resource-group rg-iauto-lab4 `
  --template-file infra\bicep\foundry-search\main.bicep `
  --parameters infra\bicep\foundry-search\main.bicepparam
```

If your subscription already has a Free Azure AI Search service, change `searchSku` in `main.bicepparam` to `basic` and redeploy.

Capture outputs:

```powershell
$deployment = az deployment group show --resource-group rg-iauto-lab4 --name main --query properties.outputs
$deployment
```

Set local environment values from the outputs:

```powershell
Copy-Item src\foundry-agent\.env.example src\foundry-agent\.env
# Edit .env: AZURE_SEARCH_ENDPOINT, AZURE_SEARCH_INDEX, APPLICATIONINSIGHTS_CONNECTION_STRING.
```

## 2. Install the agent package

```powershell
Set-Location src\foundry-agent
uv venv --python 3.12
uv pip install -e ".[dev,ai]"
```

## 3. Ingest the migrated knowledge base

The sample KB docs are committed in `iauto_foundry_agent\knowledge`.

```powershell
uv run iauto-foundry --env-file .env ingest
```

Expected result: `Uploaded <n> sample knowledge chunks to index 'iauto-foundry-kb'.`

## 4. Run locally with GitHub Models (free default)

Edit `src\foundry-agent\.env`:

```text
IAUTO_AGENT_RUNTIME=modular
INFERENCE_PROVIDER=github
GITHUB_TOKEN=<your GitHub token>
GITHUB_MODELS_ENDPOINT=https://models.github.ai/inference
GITHUB_MODELS_MODEL=openai/gpt-4o-mini
```

Ask grounded questions:

```powershell
uv run iauto-foundry --env-file .env ask "What is the approval limit for expenses?"
uv run iauto-foundry --env-file .env ask "How do I set up VPN?" --show-context
```

You should see an answer plus citations such as `Contoso Expense Policy — Approval Thresholds`.

## 5. Switch providers without changing code

### Azure OpenAI via the shared inference layer

```text
IAUTO_AGENT_RUNTIME=modular
INFERENCE_PROVIDER=azure_openai
AZURE_OPENAI_ENDPOINT=https://<resource>.openai.azure.com
AZURE_OPENAI_DEPLOYMENT=<deployment-name>
AZURE_OPENAI_API_VERSION=2025-04-01-preview
# AZURE_OPENAI_API_KEY is optional; omit it to use Entra ID.
```

### Azure AI Foundry OpenAI-compatible route via shared inference

```text
IAUTO_AGENT_RUNTIME=modular
INFERENCE_PROVIDER=foundry
AZURE_AI_FOUNDRY_ENDPOINT=https://<foundry-models-endpoint>
AZURE_AI_FOUNDRY_MODEL=<model-name>
# AZURE_AI_FOUNDRY_API_KEY is optional; omit it to use Entra ID.
```

### Native Agent Framework Foundry runtime

Use this when you want Agent Framework's `FoundryChatClient` against a Foundry project endpoint:

```text
IAUTO_AGENT_RUNTIME=foundry
AZURE_AI_FOUNDRY_PROJECT_ENDPOINT=https://<project>.services.ai.azure.com/api/projects/<project-name>
AZURE_AI_FOUNDRY_MODEL=<model-name>
```

Boundary: in `modular` mode the Agent Framework OpenAI-compatible client uses the raw async client from `iauto_inference`, so generation is provider-swappable. In `foundry` mode Agent Framework must use its native Foundry client for project endpoint semantics; the context summarizer still uses `iauto_inference`.

> 📋 **Evidence awareness — Module B.1.1:** Save one CLI transcript that shows the same question answered with citations after switching from GitHub Models to an Azure-hosted model. It demonstrates a migration path from low-code knowledge configuration to a code-first, Azure-operated agentic RAG pattern.

## 6. Validate code quality

```powershell
uv run ruff check .
uv run mypy iauto_foundry_agent
uv run bandit -c pyproject.toml -r iauto_foundry_agent
uv run pytest
uv run pip-audit
az bicep build --file ..\..\infra\bicep\foundry-search\main.bicep
```

## Troubleshooting

- **RBAC propagation:** Wait 5–10 minutes after deployment if ingestion returns 401/403. You need Search Index Data Contributor for ingestion and Search Index Data Reader for querying.
- **Free Search quota:** Only one Free Azure AI Search service is allowed per subscription. Set `searchSku = 'basic'` if deployment fails.
- **Preview package drift:** Agent Framework changes quickly. Check <https://learn.microsoft.com/agent-framework/> if a client class moves.
- **Provider environment:** `iauto_inference` does not accept a `system=` keyword. System instructions are the first message in the message list.
- **No citations:** Re-run `uv run iauto-foundry --env-file .env ingest`, then ask with `--show-context` to confirm retrieval returns chunks.
