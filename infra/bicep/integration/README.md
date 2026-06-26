# Hybrid Integration — Bicep IaC (`infra/bicep/integration`)

Infrastructure as Code for **Lab 6** of the *Intelligent Automation* Train-the-Trainer
course. Deploys the hybrid front door used by the lab:

```
API Management (Consumption)
        │
        ▼
Logic App Standard  ──▶  Connector Function (.NET 10 isolated)  ──▶  on-prem stub
   (workflow.json)            modular inference (IAuto.Inference)
```

All AI runs through the shared `IAuto.Inference` layer, so the provider (GitHub Models /
Azure OpenAI / Azure AI Foundry) is selected by **configuration only** — the Function app
settings carry `INFERENCE_PROVIDER` plus the provider-specific, non-secret settings; the key
flows from Key Vault via managed identity.

## Layout

| File | Scope | Purpose |
| --- | --- | --- |
| `main.bicep` | `subscription` | Creates `rg-<prefix>-<env>` and calls `workload.bicep`. Entry point for all deployments. |
| `workload.bicep` | `resourceGroup` | Wires every module together with unique, deterministic names. |
| `modules/identity.bicep` | RG | User-assigned managed identity (one identity, reused everywhere). |
| `modules/monitoring.bicep` | RG | Log Analytics workspace + Application Insights. |
| `modules/keyvault.bicep` | RG | RBAC Key Vault, `github-token` + `onprem-api-key` secrets, **Key Vault Secrets User** role for the identity. |
| `modules/function.bicep` | RG | Flex Consumption (`FC1`) Function: keyless storage, deployment container, 3 storage role assignments, `dotnet-isolated` runtime `10`, Key Vault references. |
| `modules/logicapp.bicep` | RG | Logic App Standard (`WS1`) site + plan, key-based content share, function host key wiring. |
| `modules/apim.bicep` | RG | API Management Consumption gateway, backend, API, operation and `set-backend-service` policy. |
| `params/{dev,test,prod}.bicepparam` | — | Per-environment, **non-secret** values. |

## Security model

- **Managed identity, not keys.** One user-assigned identity is granted Key Vault *Secrets
  User* and the storage data roles. Function app settings use `@Microsoft.KeyVault(...)`
  references resolved through `keyVaultReferenceIdentity`.
- **Secrets never live in source.** `gitHubToken` and `onPremApiKey` are `@secure()` params
  with empty defaults. They are supplied **only at deploy time**:
  ```bash
  az deployment sub create ... \
    --parameters gitHubToken=$GH_TOKEN onPremApiKey=$ONPREM_KEY
  ```
- **Purge protection** is parameterised: off in dev/test (easy reset), on in prod.

> 📋 **Evidence awareness:** an assessor would capture the deployed resource IDs, the Key
> Vault access-policy/RBAC assignment, and the `az deployment sub what-if` output proving the
> identity — not a connection string — is what grants access. We build the deployable
> artifact; we do not build evidence-collection tooling.

## Validate locally

```powershell
az bicep build --file main.bicep                     # compile + lint the whole graph
az bicep build-params --file params/dev.bicepparam   # validate a param file
```

## Deploy

```powershell
# Preview (what-if) — never mutates anything
az deployment sub create `
  --name lab6-dev-whatif `
  --location westeurope `
  --template-file main.bicep `
  --parameters params/dev.bicepparam `
  --parameters gitHubToken=$env:GH_TOKEN onPremApiKey=$env:ONPREM_KEY `
  --what-if

# Deploy
az deployment sub create `
  --name lab6-dev `
  --location westeurope `
  --template-file main.bicep `
  --parameters params/dev.bicepparam `
  --parameters gitHubToken=$env:GH_TOKEN onPremApiKey=$env:ONPREM_KEY
```

The `cd-infra.yml` workflow runs exactly this **what-if → deploy** sequence per environment
behind GitHub Environment approval gates, authenticating with **Azure OIDC** (no stored
credentials).

## Paid-tier upgrade path

| Lab default (free/consumption) | Production upgrade |
| --- | --- |
| APIM **Consumption** | APIM **Developer** → **Standard v2** (VNet, SLA). |
| Logic App **WS1** | **WS2/WS3** or scaled plan for throughput. |
| Function **Flex Consumption** | Higher `functionMaxInstanceCount`, or **EP** Elastic Premium for VNet + no cold start. |
| Key Vault purge protection off (dev/test) | **On everywhere**. |
| GitHub Models inference | Azure OpenAI / Azure AI Foundry — flip `inferenceProvider` + `inferenceAppSettings`. |
