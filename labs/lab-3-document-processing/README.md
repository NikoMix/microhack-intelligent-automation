# Lab 3 — Migrate invoice processing from Power Platform to Azure

In this lab you migrate a common Power Automate invoice flow to Azure Functions, Azure AI Document Intelligence, managed-identity Blob Storage, and the shared modular inference layer.

## Power Platform → Azure mapping

| Power Automate flow step | Azure-first replacement |
| --- | --- |
| Trigger: file arrives in SharePoint/Dataverse | Blob trigger on the `incoming` container |
| AI Builder document processing | Azure AI Document Intelligence `prebuilt-invoice` |
| Condition/classification step | Shared `IAuto.Inference` client using GitHub Models locally or Azure OpenAI in production |
| Write-back JSON/status | Structured result in the `processed` Blob container |
| Run history | Application Insights and Log Analytics telemetry |

📋 **Evidence awareness:** This is a Module B.1.1 platform-delivery reference architecture: managed identity, Azure-native services, infrastructure as code, and repeatable build/test gates. No extra evidence-collection busywork is required in this course.

## Prerequisites

- .NET SDK 10.0.301 or later in this repo image.
- Azure CLI with Bicep 0.44+.
- Azure Functions Core Tools v4.
- An Azure subscription where you can create resource groups, managed identities, storage, Function Apps, Application Insights, and Azure AI services.
- A GitHub token with GitHub Models access for local inference (`GITHUB_TOKEN`).

> **Windows path length:** Azure Functions builds generate deeply nested output (`obj\…\WorkerExtensions\bin\…`). On Windows, clone this repository to a short path (for example `C:\src\`) or build with `--artifacts-path` (as shown in step 4) to stay under the 260-character `MAX_PATH` limit. Linux, macOS, and GitHub Actions runners are unaffected.

## 1. Deploy the shared core

From the repository root, deploy the shared core first and keep the outputs:

```powershell
az group create --name rg-iauto-lab3 --location swedencentral
az deployment group create `
  --resource-group rg-iauto-lab3 `
  --template-file infra\bicep\core\core.bicep `
  --parameters workloadName=iauto environment=dev instance=003 deployKeyVault=false keyVaultAllowPublicAccess=true
```

Record these outputs: `identityClientId`, `identityPrincipalId`, `appInsightsConnectionString`, `logAnalyticsWorkspaceId`, and `names.managedIdentity`.

## 2. Deploy Lab 3 infrastructure

Edit `infra\bicep\doc-intelligence\main.bicepparam` and paste the core outputs. Then run:

```powershell
az bicep build --file infra\bicep\doc-intelligence\main.bicep
az deployment group create `
  --resource-group rg-iauto-lab3 `
  --template-file infra\bicep\doc-intelligence\main.bicep `
  --parameters infra\bicep\doc-intelligence\main.bicepparam
```

If `F0` capacity is unavailable for Document Intelligence in your region, change `documentIntelligenceSku` to `S0` and redeploy.

## 3. Configure local settings for GitHub Models

Copy `src\document-processing\IAuto.DocumentProcessing\local.settings.json.example` to `local.settings.json` (do not commit it). Fill in:

- `AzureWebJobsStorage__*` with the function storage endpoints.
- `DocumentStorage__blobServiceUri` and `DocumentProcessing__StorageBlobServiceUri` with the data storage Blob endpoint.
- `DocumentProcessing__DocumentIntelligenceEndpoint` with the Bicep output.
- `GITHUB_TOKEN` with your local GitHub token.

Keep the defaults:

```json
"INFERENCE_PROVIDER": "github",
"GITHUB_MODELS_ENDPOINT": "https://models.github.ai/inference",
"GITHUB_MODELS_MODEL": "openai/gpt-4o-mini"
```

## 4. Run locally

```powershell
cd src\document-processing
dotnet build .\DocumentProcessing.slnx -c Release --artifacts-path .\.artifacts
cd .\IAuto.DocumentProcessing
func start
```

In another terminal, upload an invoice PDF or image to the `incoming` container:

```powershell
az storage blob upload `
  --auth-mode login `
  --account-name <data-storage-account> `
  --container-name incoming `
  --name sample-invoice.pdf `
  --file .\sample-invoice.pdf
```

The Function calls Document Intelligence, summarizes/classifies the invoice through `IAuto.Inference`, and writes `sample-invoice.processed.json` to `processed`.

## 5. Observe results and telemetry

Read the processed JSON:

```powershell
az storage blob download `
  --auth-mode login `
  --account-name <data-storage-account> `
  --container-name processed `
  --name sample-invoice.processed.json `
  --file .\sample-invoice.processed.json
Get-Content .\sample-invoice.processed.json
```

Open Application Insights for the shared core and inspect traces/dependencies for the invocation id in the output JSON.

📋 **Evidence awareness:** For Module B.1.1, a trainer would normally capture the deployment output, processed JSON, and App Insights trace as evidence. Here, discuss where that evidence lives without turning the lab into paperwork.

## 6. Swap to Azure OpenAI

Create or reuse an Azure OpenAI chat deployment and grant the managed identity **Cognitive Services OpenAI User** on that resource. Change settings:

```json
"INFERENCE_PROVIDER": "azure_openai",
"AZURE_OPENAI_ENDPOINT": "https://<aoai-name>.openai.azure.com/",
"AZURE_OPENAI_DEPLOYMENT": "<chat-deployment>",
"AZURE_OPENAI_API_KEY": ""
```

Restart `func start` and upload another invoice. No code changes are required.

## Troubleshooting

- **`MSB3030 … .dll because it was not found` on a Windows build:** This is the 260-character `MAX_PATH` limit in the nested Functions `WorkerExtensions` output, not a genuinely missing file. Clone to a shorter directory or build with `--artifacts-path` (see step 4). To opt into long paths system-wide: `git config --system core.longpaths true` and set the `HKLM\SYSTEM\CurrentControlSet\Control\FileSystem\LongPathsEnabled` registry value to `1`.
- **Authentication:** Run `az login` locally. In Azure, confirm the Function App uses the shared user-assigned managed identity client id.
- **RBAC delay:** Storage and Document Intelligence role assignments can take several minutes to propagate. Retry after 5–10 minutes before changing code.
- **Blob trigger does not fire:** Confirm the blob is in `incoming`, `DocumentStorage__blobServiceUri` is the data account, and app setting `DocumentProcessing__IncomingContainer` is `incoming`.
- **Cold start:** Flex Consumption can need a short warm-up. Check live logs and App Insights before re-uploading many files.
- **Provider env:** GitHub Models requires `GITHUB_TOKEN`. Azure OpenAI with Entra requires endpoint, deployment, and RBAC; leave `AZURE_OPENAI_API_KEY` empty for keyless auth.
