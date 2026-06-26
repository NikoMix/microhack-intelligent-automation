# Lab 3 infrastructure — Document Intelligence + Flex Consumption Functions

Bicep that provisions the **Azure-first** target for the migrated document-processing
flow: an Azure Functions app (Flex Consumption, .NET 10 isolated) bound to **Azure AI
Document Intelligence**, with identity-based connections, a review queue for the
human-in-the-loop step, and workspace-based Application Insights.

> Part of **Lab 3** (`labs/lab-3-document-processing/`). Module **B.1.1** — unattended-RPA
> migration target. See the lab guide for the end-to-end walkthrough.

## What gets deployed

| Resource | Type | Notes |
| --- | --- | --- |
| User-assigned managed identity | `Microsoft.ManagedIdentity/userAssignedIdentities` | Single identity used for every connection (Entra ID). |
| Log Analytics workspace | `Microsoft.OperationalInsights/workspaces` | Backs workspace-based App Insights. |
| Application Insights | `Microsoft.Insights/components` | Workspace-based; Entra-authenticated ingestion. |
| Storage account | `Microsoft.Storage/storageAccounts` | `allowSharedKeyAccess: false`, TLS 1.2. Contains the deployment container, an `incoming-documents` container, and the `document-review` queue. |
| Document Intelligence | `Microsoft.CognitiveServices/accounts` (kind `FormRecognizer`) | `disableLocalAuth: true` → Entra ID only. `customSubDomainName` set for token auth. |
| Flex Consumption plan | `Microsoft.Web/serverfarms` (`FC1`) | Scales to zero. |
| Function App | `Microsoft.Web/sites` | `dotnet-isolated` runtime `version: '10'`, identity-based deployment storage. |
| Role assignments | `Microsoft.Authorization/roleAssignments` | Least-privilege (see below). |

### Identity & least-privilege RBAC

Every connection uses the user-assigned managed identity through
`DefaultAzureCredential` (`AZURE_CLIENT_ID` is set to the identity's client ID). The
template assigns only what the app needs:

| Role | Scope | Why |
| --- | --- | --- |
| Storage Blob Data Owner | Storage account | Host storage + read `incoming-documents`. |
| Storage Queue Data Contributor | Storage account | Write/read the review queue. |
| Cognitive Services User | Document Intelligence | Call the analyze API with a token. |
| Monitoring Metrics Publisher | Application Insights | Entra-authenticated telemetry. |

> No keys or connection strings are emitted by this template or written to app settings.

## Prerequisites

- Azure CLI `2.87+` with the Bicep CLI (`az bicep version`).
- An Azure subscription and permission to create role assignments (Owner or
  User Access Administrator on the target resource group).
- Run the commands from this folder.

## Deploy

```bash
az group create -n rg-lab3-doc -l swedencentral
az deployment group create \
  -g rg-lab3-doc \
  -f main.bicep \
  -p main.bicepparam
```

Capture the outputs (function app name, Document Intelligence endpoint, queue and
container names) — the lab uses them for app deployment and validation.

```bash
az deployment group show -g rg-lab3-doc -n main \
  --query properties.outputs -o jsonc
```

## Wire the blob trigger (Event Grid) — post-deploy

Flex Consumption requires the **Event Grid** blob-trigger source (the legacy
container-polling source is not supported). After you deploy the **function code**,
create an Event Grid subscription from the storage account to the blob extension
endpoint. The blob-extension system key only exists once the app and its functions
are deployed, so this is a post-deployment step:

```bash
FUNC=<functionAppName>
RG=rg-lab3-doc
STORAGE=<storageAccountName>

# 1. Get the blob-extension system key (after code deploy)
KEY=$(az functionapp keys list -g $RG -n $FUNC \
  --query "systemKeys.blobs_extension" -o tsv)

ENDPOINT="https://$FUNC.azurewebsites.net/runtime/webhooks/blobs?functionName=Host.Functions.DocumentBlobTriggerFunction&code=$KEY"

# 2. Subscribe to BlobCreated events for the incoming-documents container
STORAGE_ID=$(az storage account show -g $RG -n $STORAGE --query id -o tsv)
az eventgrid event-subscription create \
  --name lab3-incoming-documents \
  --source-resource-id $STORAGE_ID \
  --endpoint-type webhook \
  --endpoint "$ENDPOINT" \
  --included-event-types Microsoft.Storage.BlobCreated \
  --subject-begins-with "/blobServices/default/containers/incoming-documents/"
```

For local development you can instead use the polling source
(`Source = BlobTriggerSource.LogsAndContainerScan`) against the Azurite emulator —
see the lab guide. The committed function uses the Event Grid source for the
deployed (Azure) path.

## Enabling LLM post-processing (optional)

The insights step is **off by default** (`DocumentProcessing__EnableInsights=false`).
To turn it on without redeploying infrastructure, set the toggle plus the modular
inference provider settings on the Function App. The free default is GitHub Models:

```bash
az functionapp config appsettings set -g rg-lab3-doc -n <functionAppName> --settings \
  DocumentProcessing__EnableInsights=true \
  INFERENCE_PROVIDER=github \
  GITHUB_MODELS_MODEL=openai/gpt-4o-mini
# GITHUB_TOKEN should come from Key Vault or a secured setting — never commit it.
```

Azure OpenAI and Azure AI Foundry are selected purely by changing `INFERENCE_PROVIDER`
and the matching endpoint settings (see the root README inference contract). When you
use Azure OpenAI or Foundry with Entra ID, grant the managed identity **Cognitive
Services OpenAI User** on that resource.

## Parameters

| Parameter | Default | Description |
| --- | --- | --- |
| `namePrefix` | `lab3doc` | 3–11 char lowercase alphanumeric prefix for resource names. |
| `location` | resource group location | Azure region. |
| `instanceMemoryMB` | `2048` | Flex Consumption per-instance memory (512 / 2048 / 4096). |
| `maximumInstanceCount` | `100` | Max scale-out instances (40–1000). |
| `documentIntelligenceSku` | `S0` | Document Intelligence SKU (no free tier for the resource). |
| `enableInsights` | `false` | Toggle the modular-inference LLM step. |
| `incomingDocumentsContainerName` | `incoming-documents` | Blob trigger source container. |
| `deploymentStorageContainerName` | `app-package` | Flex Consumption deployment container. |
| `reviewQueueName` | `document-review` | Human-in-the-loop review queue. |
| `tags` | `{}` | Resource tags. |

## API versions

API versions are pinned to current GA releases validated against the installed Bicep
CLI (`az bicep build` is warning-free). Bump them deliberately and re-run
`az bicep build` when upgrading.

## Clean up

```bash
az group delete -n rg-lab3-doc --yes --no-wait
```

> 📋 **Evidence awareness:** an assessor for the specialization would expect proof the
> migrated workload runs on Azure with secure-by-default configuration — for example a
> screenshot or `az` export showing `allowSharedKeyAccess=false` and `disableLocalAuth=true`,
> the role assignments scoped to the managed identity, and the deployment outputs. This lab
> teaches you to *produce* that posture; capturing the screenshot/export is the evidence step.
