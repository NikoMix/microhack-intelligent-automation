# Lab 4 - Migrate a Copilot Studio Knowledge Agent to an Agent Framework RAG Agent

In this lab you move a typical **Copilot Studio knowledge agent** pattern into a code-first, Azure-ready architecture: **Microsoft Agent Framework** orchestrates the agent, a **license-free offline BM25 retriever** grounds answers with zero Azure by default, **Azure AI Search** is the optional managed-retrieval upgrade, **Azure AI Foundry / Azure OpenAI / GitHub Models** generate grounded answers, and **Application Insights** captures telemetry.

You run the whole lab **offline first** - GitHub Models (free) plus the built-in BM25 retriever over the committed knowledge base - then **upgrade to Azure AI Search** when you want managed, scalable retrieval. This mirrors the course's free-default, Azure-on-demand principle used in every other lab.

## What you build

- A Python 3.12 Agent Framework app with **pluggable retrieval** behind a single `Retriever` protocol:
  - a **license-free offline BM25 `KeywordRetriever`** (zero Azure, no extra dependency) - the free default,
  - an **`AzureSearchRetriever`** for the managed upgrade,
  - citations using document title + section,
  - `iauto_inference` provider-swappable summarization and generation,
  - an optional native `FoundryChatClient` runtime.
- (Optional upgrade) an Azure AI Search index with sample HR/IT/procurement knowledge articles, plus an Azure AI Services / Foundry account and Foundry project.

## Migration framing

| Copilot Studio concept | Azure-first replacement in this lab |
|---|---|
| Knowledge sources | Markdown docs ranked by offline BM25 (free) or ingested into Azure AI Search (upgrade) |
| Topics / generative orchestration | Microsoft Agent Framework instructions + retrieval tool |
| Copilot Studio answer grounding | RAG prompt with citations from the pluggable retriever |
| Studio analytics | OpenTelemetry traces exported to Application Insights |
| Environment variables / connections | Managed identity + RBAC for the Azure upgrade; `.env` for local dev |

Agent Framework replaces Copilot Studio's managed orchestration loop. Your Python code owns when to retrieve, summarize, call tools, route generation, and which retrieval backend to use.

> 📋 **Evidence awareness - Module B.1.1:** This lab is a lightweight reference architecture for "Power Platform + Azure delivery capability": Copilot Studio knowledge agent to an Agent Framework RAG agent (offline BM25, then Azure AI Search) + managed identity + telemetry. Capture a sample grounded answer (offline) and, for the upgrade, the deployed architecture diagram as evidence.

## Prerequisites

**Required (offline path):**

- Python 3.12 and `uv`.
- A GitHub token with access to GitHub Models (free) - or any Azure OpenAI / Foundry model.

**Optional (Azure AI Search upgrade only):**

- Azure subscription and rights to create a resource group deployment and role assignments.
- Azure CLI with Bicep CLI 0.44+ (`az bicep version`).

From repo root, stay inside `src\foundry-agent`, `infra\bicep\foundry-search`, and `labs\lab-4-foundry-agent` for lab work.

## 1. Install the agent package

```powershell
Set-Location src\foundry-agent
uv venv --python 3.12
uv pip install -e ".[dev,ai]"
```

No Azure resources are required for the steps below.

## 2. Run offline first with GitHub Models (zero Azure)

Create your local env from the offline-first template and add only a GitHub token:

```powershell
Copy-Item .env.example .env
# Edit .env and set GITHUB_TOKEN=<your GitHub token>. Leave the Azure blocks commented out.
```

The retriever defaults to the **license-free offline BM25 `KeywordRetriever`** over the knowledge base committed in `iauto_foundry_agent\knowledge` - no Azure AI Search, no ingestion, no network beyond the model call.

```powershell
uv run iauto-foundry --env-file .env ask "What is the approval limit for expenses?"
uv run iauto-foundry --env-file .env ask "How do I set up VPN?" --show-context
```

You should see an answer plus citations such as `Contoso Expense Policy - Approval Thresholds`. The `--retriever` flag controls the backend (`auto` is the default):

- `--retriever offline` - always use the built-in BM25 retriever (zero Azure).
- `--retriever auto` - use Azure AI Search when `AZURE_SEARCH_ENDPOINT` is set, otherwise offline BM25.
- `--retriever azure` - force Azure AI Search (requires the upgrade in step 4).

## 3. Switch generation providers without changing code

Retrieval stays offline while you swap the model provider through the shared `iauto_inference` layer.

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

> 📋 **Evidence awareness - Module B.1.1:** Save one CLI transcript that shows the same question answered with citations after switching from GitHub Models to an Azure-hosted model - still using offline retrieval. It demonstrates a migration path from low-code knowledge configuration to a code-first, Azure-operated agentic RAG pattern.

## 4. (Optional upgrade) Move retrieval to Azure AI Search

Swap the offline BM25 index for managed, scalable Azure AI Search when you need enterprise retrieval.

Provision the Foundry/Search resources from repo root:

```powershell
az group create --name rg-iauto-lab4 --location swedencentral
az deployment group create `
  --resource-group rg-iauto-lab4 `
  --template-file infra\bicep\foundry-search\main.bicep `
  --parameters infra\bicep\foundry-search\main.bicepparam
```

If your subscription already has a Free Azure AI Search service, change `searchSku` in `main.bicepparam` to `basic` and redeploy.

Capture outputs and update `.env`:

```powershell
az deployment group show --resource-group rg-iauto-lab4 --name main --query properties.outputs
# In src\foundry-agent\.env, uncomment and set:
#   AZURE_SEARCH_ENDPOINT, AZURE_SEARCH_INDEX, APPLICATIONINSIGHTS_CONNECTION_STRING
```

Ingest the sample knowledge base into the index, then ask with the Azure backend:

```powershell
uv run iauto-foundry --env-file .env ingest
uv run iauto-foundry --env-file .env ask "What is the approval limit for expenses?" --retriever azure
```

Expected ingest result: `Uploaded <n> sample knowledge chunks to index 'iauto-foundry-kb'.` With `AZURE_SEARCH_ENDPOINT` set, `--retriever auto` (the default) also uses Azure AI Search.

## 5. (Optional) Native Agent Framework Foundry runtime

Use this when you want Agent Framework's `FoundryChatClient` against a Foundry project endpoint:

```text
IAUTO_AGENT_RUNTIME=foundry
AZURE_AI_FOUNDRY_PROJECT_ENDPOINT=https://<project>.services.ai.azure.com/api/projects/<project-name>
AZURE_AI_FOUNDRY_MODEL=<model-name>
```

Boundary: in `modular` mode the Agent Framework OpenAI-compatible client uses the raw async client from `iauto_inference`, so generation is provider-swappable. In `foundry` mode Agent Framework must use its native Foundry client for project endpoint semantics; the context summarizer still uses `iauto_inference`. Retrieval is independent of the runtime - offline BM25 or Azure AI Search applies in both.

## 6. Validate code quality

```powershell
uv run ruff check .
uv run ruff format --check .
uv run mypy .
uv run bandit -c pyproject.toml -r iauto_foundry_agent
uv run pytest
uv run pip-audit
az bicep build --file ..\..\infra\bicep\foundry-search\main.bicep
```

## Troubleshooting

- **Offline first:** If `ask` fails, confirm `GITHUB_TOKEN` is set and the Azure blocks in `.env` are commented out (so `--retriever auto` stays offline). No Azure resources are needed for steps 1-3.
- **No citations (offline):** Ask with `--show-context` to confirm the BM25 retriever returns chunks; broaden your query wording to match the committed knowledge articles.
- **RBAC propagation (Azure upgrade):** Wait 5-10 minutes after deployment if ingestion returns 401/403. You need Search Index Data Contributor for ingestion and Search Index Data Reader for querying.
- **Free Search quota:** Only one Free Azure AI Search service is allowed per subscription. Set `searchSku = 'basic'` if deployment fails.
- **Preview package drift:** Agent Framework changes quickly. Check <https://learn.microsoft.com/agent-framework/> if a client class moves.
- **Provider environment:** `iauto_inference` does not accept a `system=` keyword. System instructions are the first message in the message list.