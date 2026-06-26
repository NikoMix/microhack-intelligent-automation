# `foundry-search` — Azure footprint for the Lab 4 agent

Infrastructure as Code (Bicep) that provisions everything the grounded knowledge agent needs to
run its **Azure AI Search** RAG path and its **Azure OpenAI / Azure AI Foundry** inference path,
with **Entra ID** auth and **OpenTelemetry → Azure Monitor** telemetry.

> This deploys the *Azure upgrade* for Lab 4. The lab runs end-to-end with **zero Azure** first
> (local BM25 index + free GitHub Models); deploy this only when you reach the Azure section.

## What it deploys

| Module | Resource | Purpose | Default tier |
| --- | --- | --- | --- |
| `modules/search.bicep` | Azure AI Search | RAG retrieval backend (`RETRIEVER_BACKEND=azure_search`) | `basic` |
| `modules/openai.bicep` | Azure AI Foundry / Azure OpenAI (`AIServices`) | Chat (+ optional embedding) model; serves `azure_openai` **and** `foundry` providers | `S0`, `gpt-4o-mini` |
| `modules/monitoring.bicep` | Log Analytics + Application Insights | OpenTelemetry sink | `PerGB2018`, 1 GB/day cap |
| `modules/identity.bicep` | User-assigned managed identity | Entra ID auth for the agent runtime | — |
| `modules/roles.bicep` | RBAC role assignments | Least-privilege access | — |

### Least-privilege RBAC

The **agent identity** receives exactly what the runtime needs:

- **Search Index Data Reader** on the search service (query the index — not author it).
- **Cognitive Services OpenAI User** on the account (call the model).
- **Monitoring Metrics Publisher** on Application Insights (publish telemetry via Entra ID).

An optional **developer principal** (`developerPrincipalId`) receives index-authoring rights
(**Search Index Data Contributor** + **Search Service Contributor**) and **Cognitive Services
OpenAI User**, so you can create/load the index and run the agent locally under your own identity.

## Prerequisites

- Azure CLI `2.87+` with the Bicep CLI (`az bicep version`).
- An Azure subscription and a resource group: `az group create -n rg-lab4 -l swedencentral`.
- Quota for your chosen chat model + SKU in the target region.

## Deploy

```bash
# Optional: grant yourself data-plane rights for hands-on index loading + local runs.
az ad signed-in-user show --query id -o tsv   # paste into developerPrincipalId in main.bicepparam

az deployment group create \
  --resource-group rg-lab4 \
  --template-file main.bicep \
  --parameters main.bicepparam
```

Validate before deploying with a what-if:

```bash
az deployment group what-if -g rg-lab4 -f main.bicep -p main.bicepparam
```

## Outputs → `.env`

Output names match the agent's environment-variable contract, so you can map them directly:

```bash
az deployment group show -g rg-lab4 -n main \
  --query "properties.outputs" -o jsonc
```

| Output | Maps to env var | Notes |
| --- | --- | --- |
| `RETRIEVER_BACKEND` | `RETRIEVER_BACKEND` | `azure_search` |
| `AZURE_SEARCH_ENDPOINT` | `AZURE_SEARCH_ENDPOINT` | |
| `AZURE_SEARCH_INDEX` | `AZURE_SEARCH_INDEX` | |
| `AZURE_OPENAI_ENDPOINT` | `AZURE_OPENAI_ENDPOINT` | with `INFERENCE_PROVIDER=azure_openai` |
| `AZURE_OPENAI_DEPLOYMENT` | `AZURE_OPENAI_DEPLOYMENT` | |
| `AZURE_AI_FOUNDRY_ENDPOINT` | `AZURE_AI_FOUNDRY_ENDPOINT` | with `INFERENCE_PROVIDER=foundry` |
| `AZURE_AI_FOUNDRY_MODEL` | `AZURE_AI_FOUNDRY_MODEL` | |
| `APPLICATIONINSIGHTS_CONNECTION_STRING` | `APPLICATIONINSIGHTS_CONNECTION_STRING` | **sensitive** — keep out of source control |
| `AZURE_CLIENT_ID` | `AZURE_CLIENT_ID` | set on Azure compute so `DefaultAzureCredential` picks the agent identity |

## Security notes

- **Entra ID first.** Keys stay enabled in the classroom (`disableLocalAuth=false`) but RBAC is
  *always* granted, so you can flip `disableLocalAuth=true` for an Entra-only posture with no other
  change. With keys disabled, omit `AZURE_SEARCH_API_KEY` / `AZURE_OPENAI_API_KEY` and the agent
  falls back to `DefaultAzureCredential`.
- **No secrets in IaC.** The only sensitive output is the App Insights connection string; never
  commit it. Deployment outputs live in the deployment history, not in the repo.
- **Cost guardrails.** Log Analytics has a 1 GB/day ingestion cap; the chat deployment is 8K TPM.

## Teardown

```bash
az group delete -n rg-lab4 --yes --no-wait
```

## Validate the templates locally

```bash
az bicep build --file main.bicep            # compiles clean (no warnings)
az bicep build-params --file main.bicepparam
```

> 📋 **Evidence awareness:** the specialization's *platform delivery capability* (B.1.1) expects a
> reference architecture + IaC. An assessor would capture this template set, a successful
> `what-if`/deployment, and the resulting RBAC assignments as evidence — no extra tooling required.
