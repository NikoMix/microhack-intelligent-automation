# Lab 6 — Hybrid integration: Power Automate gateway flow to Azure

In this lab you migrate a representative Power Automate flow that depended on an on-premises data gateway into Azure integration services:

- **Before:** Power Automate receives an order or approval payload, calls through the on-premises data gateway, applies light business logic, and returns a response.
- **After:** API Management fronts a managed-identity Azure Functions integration bridge. Logic Apps Standard orchestrates the request, calls the bridge, branches on the routing result, and responds. The bridge enriches the event through the shared `IAuto.Inference` module using GitHub Models by default.

## What you build

| Layer | Azure replacement | Lab artifact |
| --- | --- | --- |
| Power Automate trigger | Logic Apps Standard request trigger | `src/hybrid-integration/workflows/power-platform-migration/workflow.json` |
| Gateway/API facade | API Management Consumption | `infra/bicep/integration/main.bicep` |
| Inline flow logic | .NET isolated Azure Functions bridge | `src/hybrid-integration/src/IAuto.HybridIntegration.Functions` |
| ALM | GitHub Actions + Bicep + OIDC | `.github/workflows/ci.yml`, `.github/workflows/deploy.yml` |

## Prerequisites

- .NET 10 SDK. The CI workflow also installs the .NET 8 SDK because the Azure Functions isolated worker generates a `net8.0` `WorkerExtensions` project during build.
- Azure CLI with Bicep CLI 0.44 or later.
- Azure Functions Core Tools v4 for local execution.
- A GitHub token with access to GitHub Models.
- Azure subscription permissions to create resource groups, managed identities, API Management, Function Apps, Logic Apps Standard, storage, role assignments, Log Analytics, Application Insights, and Key Vault.

> **Windows path length:** Azure Functions builds generate deeply nested output (`obj\…\WorkerExtensions\bin\…`). On Windows, clone this repository to a short path (for example `C:\src\`) or build with `--artifacts-path` to stay under the 260-character `MAX_PATH` limit. Linux, macOS, and GitHub Actions runners are unaffected.

## 1. Run the integration bridge locally

```powershell
cd src\hybrid-integration\src\IAuto.HybridIntegration.Functions
Copy-Item local.settings.json.example local.settings.json
# Edit local.settings.json and set GITHUB_TOKEN.
func start
```

In another terminal, post a migrated business event:

```powershell
$body = @{
  eventType = 'approval.requested'
  sourceSystem = 'sap'
  customerId = 'contoso'
  amount = 12000
  currency = 'EUR'
} | ConvertTo-Json

Invoke-RestMethod -Method Post `
  -Uri 'http://localhost:7071/api/business-events' `
  -Headers @{ 'x-correlation-id' = 'lab6-local-001' } `
  -Body $body `
  -ContentType 'application/json'
```

Expected result: `accepted=true`, an enrichment summary from the configured model, and `routing.priority=High`.

## 2. Deploy the Azure integration foundation

From the repo root:

```powershell
az login
az account set --subscription '<subscription-id>'
az group create --name rg-iauto-dev-006 --location swedencentral
az deployment group create `
  --resource-group rg-iauto-dev-006 `
  --template-file infra\bicep\integration\main.bicep `
  --parameters infra\bicep\integration\main.bicepparam
```

The deployment composes the shared core and adds:

- Flex Consumption Function App using the shared user-assigned managed identity.
- Logic Apps Standard site on WS1 with managed-identity storage settings.
- API Management Consumption facade with rate limiting, correlation propagation, and a managed-identity backend-auth policy sample.
- Least-privilege role assignments via the shared role assignment module.

> The Function App does not store model keys. For cloud inference, use managed identity for Azure OpenAI/Foundry or set local-only GitHub Models credentials during development.

## 3. Exercise the Logic Apps Standard workflow

1. Open the deployed Logic Apps Standard resource in the Azure portal or VS Code Logic Apps extension.
2. Add/import the workflow definition from `src\hybrid-integration\workflows\power-platform-migration\workflow.json` if your deployment process has not packaged workflows yet.
3. Confirm the app setting `BRIDGE_API_BASE_URL` points to the Function App host name.
4. Run the request trigger with the sample payload above.
5. Confirm the branch returns:
   - `202 queued-for-approval` for high-value or approval events.
   - `200 processed` for standard orders.

## 4. ALM and CI/CD walkthrough

### CI

Review `.github\workflows\ci.yml`:

- Discovers and builds/tests/formats all `.slnx` or `.sln` files under `src`.
- Discovers Python `pyproject.toml` packages and runs `uv`, Ruff, mypy, Bandit, and pytest.
- Builds every Bicep file under `infra\bicep`.
- Runs CodeQL for C# and Python.

📋 **Evidence awareness — Module B.3.2:** repeatable Bicep plus CI gates provide the ALM evidence trail that replaces manual Power Platform export/import steps.

### Manual deploy with OIDC

1. In Azure, create or reuse a Microsoft Entra app registration / workload identity used by GitHub Actions.
2. Add a federated credential for this repository, branch or environment, and the `dev` GitHub Environment.
3. Grant least-privilege Azure RBAC at the target resource group or subscription scope.
4. In the repository or `dev` environment, configure:
   - `AZURE_CLIENT_ID`
   - `AZURE_TENANT_ID`
   - `AZURE_SUBSCRIPTION_ID`
5. Trigger **Deploy lab environment** from the Actions tab and choose `lab-6`.

📋 **Evidence awareness — Module B.1.1:** the environment, OIDC trust, CodeQL results, and deployment history give trainers a lightweight audit trail without adding separate evidence-collection tooling.

## 5. Security recap

- Managed identity and `DefaultAzureCredential` are preferred over secrets.
- Storage public blob access is disabled, TLS 1.2 is enforced, and shared key access is disabled by the shared storage module.
- APIM provides subscription control, rate limiting, correlation headers, and a managed-identity backend-auth policy sample.
- CI runs CodeQL and dependency vulnerability checks.
- Bicep keeps environments repeatable and reviewable.

## Troubleshooting

| Symptom | Check |
| --- | --- |
| OIDC login fails | Verify the federated credential subject matches the repository, branch/environment, and workflow trigger. Confirm `AZURE_CLIENT_ID`, `AZURE_TENANT_ID`, and `AZURE_SUBSCRIPTION_ID` are available in the `dev` environment. |
| APIM deployment is slow | Consumption APIM can take several minutes to provision. Re-run the deployment if Azure reports a transient provisioning conflict. |
| Logic Apps Standard cannot start | Confirm the storage account exists, RBAC propagation completed, and the Logic App has `AzureWebJobsStorage__accountName`, `AzureWebJobsStorage__credential=managedidentity`, and `AzureWebJobsStorage__clientId`. |
| Function cannot call inference locally | Set `GITHUB_TOKEN` in `local.settings.json`, or switch `INFERENCE_PROVIDER` to `azure_openai` / `foundry` with the shared environment variables. |
| RBAC errors after deployment | Wait a few minutes for role assignment propagation, then restart the Function App and Logic App. |
| Windows build fails with `MSB3030 … .dll because it was not found` | This is the 260-character `MAX_PATH` limit in the nested Functions `WorkerExtensions` output, not a genuinely missing file. Clone to a short path (e.g. `C:\src\`) or build with `--artifacts-path`. Optionally enable long paths: `git config --system core.longpaths true` plus the `LongPathsEnabled` registry value. |
