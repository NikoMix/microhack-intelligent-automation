# Lab 3 — Migrate an unattended document-processing flow to Azure

**From Power Platform to Azure — Intelligent Automation with GitHub Agents, Skills & MCP**
Module **B.1.1** · Buildable lab · ~75–90 minutes

You inherit an **unattended** Power Automate cloud flow that uses **AI Builder** to read
incoming invoices, then routes low-confidence results to a person for review. In this lab
you migrate it to an **Azure-first** design: **Azure Functions (.NET 10 isolated)** +
**Azure AI Document Intelligence**, with a human-in-the-loop review queue and **modular
inference** for optional LLM post-processing.

---

## Objectives

By the end of this lab you can:

1. Explain why an unattended RPA + AI Builder flow maps cleanly onto **event-driven Azure
   Functions + Document Intelligence**, and name the trade-offs.
2. Build and run a **.NET 10 isolated** Functions app with a **blob trigger** (Event Grid
   source) and an **HTTP trigger** that share one processing pipeline.
3. Call **Azure AI Document Intelligence** (`prebuilt-invoice` / `prebuilt-layout`) behind a
   testable abstraction, authenticating with **Entra ID** (`DefaultAzureCredential`).
4. Implement a **confidence-threshold + required-field** gate that auto-approves or routes a
   document to a **human-in-the-loop** review queue.
5. Add **optional LLM post-processing** (summarize/classify) that runs on **GitHub Models,
   Azure OpenAI, or Azure AI Foundry by configuration only**, reusing the shared inference
   layer.
6. Provision the target with **Bicep** (Flex Consumption, identity-based, least-privilege
   RBAC) and validate the engineering bar (build, format, tests, vulnerability audit).

---

## How this maps to Module B

| Module B requirement | Where it shows up in this lab |
| --- | --- |
| **B.1.1 Platform delivery capability** — deliver an Azure reference architecture for a migrated automation | The whole lab: an unattended document flow re-platformed onto Functions + Document Intelligence with IaC. |
| Modular, provider-agnostic AI | Step 8 — LLM insights via `IChatClient` from `ChatClientFactory.CreateFromEnvironment()`. |
| Secure-by-default Azure | Step 9 — Bicep with `DefaultAzureCredential`, `allowSharedKeyAccess=false`, `disableLocalAuth=true`, scoped RBAC. |
| ALM / quality bar | Step 5 & Validation — analyzers, `TreatWarningsAsErrors`, `dotnet format`, xUnit, `dotnet list package --vulnerable`. |

> Other Module B areas (B.2.x discovery sizing, B.3.1 governance, B.4.x operate) are covered
> as **evidence-awareness callouts** in their own labs — this lab teaches the buildable B.1.1
> target.

---

## The source flow (what you are migrating)

| Power Automate + AI Builder (source) | Azure target (this lab) |
| --- | --- |
| Unattended cloud flow, **When a file is created** (SharePoint/OneDrive) | **Blob trigger** on `incoming-documents` (Event Grid source) |
| **AI Builder** *Extract information from invoices* | **Azure AI Document Intelligence** `prebuilt-invoice` |
| Condition on confidence → branch | `ReviewRouting` — confidence threshold + required fields |
| **Approvals** connector → reviewer | **Storage queue** review message + `ReviewQueueFunction` notification stub |
| Premium connectors / per-flow licensing | **Flex Consumption** Functions (scale-to-zero) + free GitHub Models default |
| Manual run history as “evidence” | OpenTelemetry → Application Insights |

---

## Prerequisites

- **.NET SDK 10.0+** (`dotnet --version`).
- **Azure Functions Core Tools v4** (`func --version`) for local run and publish.
- **Azure CLI 2.87+** with Bicep (`az bicep version`), and an Azure subscription
  (only needed for Steps 9–12 — everything else runs locally and free).
- **Azurite** storage emulator (bundled with the Azure Functions / Storage VS Code
  extensions, or `npm i -g azurite`).
- A **GitHub personal access token** with `models: read` for the free GitHub Models
  provider (only needed if you enable insights in Step 8).
- **Python 3.12+** (only to regenerate the sample invoice; the PDF is already committed).

> ⚠️ **Windows long-path note (important).** The Azure Functions Worker SDK generates a
> deeply nested inner build path. On Windows with `LongPathsEnabled=0`, a build from a deep
> folder can fail with **MSB3030** (“could not copy … Worker.Extensions.dll”). Fix it once:
>
> ```powershell
> # Enable OS + Git long paths (admin shell)
> git config --system core.longpaths true
> New-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem" `
>   -Name LongPathsEnabled -Value 1 -PropertyType DWORD -Force
> ```
>
> If you cannot change machine policy, build from a short path by mapping a drive:
> `subst W: <repo-root>` then build from `W:\src\document-processing`. This is a Windows
> path-length quirk, **not** a code or .NET 10 issue.

---

## Solution layout

```
src/document-processing/
  IAuto.DocumentProcessing/            # core library (testable; no Functions types)
    Abstractions/                      # IDocumentAnalyzer, IApprovalQueueWriter, ...
    DocumentIntelligence/              # analyzer + result mapper (Azure SDK)
    Insights/                          # ChatInsightGenerator (modular inference) + Null
    HumanInTheLoop/                    # ReviewRouting + StorageQueueApprovalWriter
    Pipeline/                          # DocumentProcessingPipeline (orchestration)
    Telemetry/                         # ActivitySource + Meter
    DependencyInjection/               # AddDocumentProcessing(IConfiguration)
  IAuto.DocumentProcessing.Functions/  # isolated host: blob + HTTP + review-queue triggers
  IAuto.DocumentProcessing.Tests/      # xUnit, fakes only (no network)
infra/bicep/doc-intelligence/          # Flex Consumption + Document Intelligence (Bicep)
labs/lab-3-document-processing/        # this guide + .env.example + samples/
```

The host stays thin: triggers deserialize input and call `IDocumentProcessingPipeline`.
All logic lives in the library so it can be unit-tested without Azure.

---

## Steps

### 1. Restore and orient

```bash
cd src/document-processing
dotnet restore IAuto.DocumentProcessing.slnx
```

Open `Pipeline/DocumentProcessingPipeline.cs` — read the flow: **analyze → optional
insights → route → auto-approve or enqueue**. Note it never references a concrete provider.

### 2. Understand the abstractions

Skim `Abstractions/`. The pipeline depends on `IDocumentAnalyzer`,
`IDocumentInsightGenerator`, and `IApprovalQueueWriter`. Tests swap in fakes; production
binds the Azure-backed implementations in `DependencyInjection/`.

### 3. Configure local settings

```bash
cd IAuto.DocumentProcessing.Functions
cp local.settings.json.example local.settings.json   # Windows: Copy-Item
```

Edit `local.settings.json`:

- `DocumentIntelligence:Endpoint` → your Document Intelligence endpoint. Leave
  `DocumentIntelligence:ApiKey` empty to use **Entra ID** (`az login`); set it only for a
  quick classroom key fallback.
- Leave `DocumentProcessing:EnableInsights` = `false` for now.
- `AzureWebJobsStorage` stays `UseDevelopmentStorage=true` (Azurite).

> No Document Intelligence resource yet? You can still build, unit-test, and exercise the
> HTTP trigger’s validation path. Provision the real resource in Step 9, or create one
> standalone with `az cognitiveservices account create --kind FormRecognizer --sku S0`.

### 4. Build

```bash
cd ..                      # src/document-processing
dotnet build IAuto.DocumentProcessing.slnx -c Release
```

Expect **0 warnings, 0 errors** (analyzers + `TreatWarningsAsErrors` are on). Windows deep
paths: see the long-path note and build from `W:` if you hit MSB3030.

### 5. Run the tests

```bash
dotnet test IAuto.DocumentProcessing.slnx -c Release
```

All tests use **fakes** — no Azure, no network. Read `ReviewRoutingTests.cs` to see the
auto-approve vs. review boundary expressed as tests.

### 6. Run locally and smoke-test the HTTP trigger

Start Azurite (e.g. `azurite --silent`), then:

```bash
cd IAuto.DocumentProcessing.Functions
func start
```

In another terminal, send the sample invoice to the HTTP trigger:

```bash
curl -s -X POST \
  "http://localhost:7071/api/documents?name=sample-invoice.pdf&model=prebuilt-invoice" \
  -H "Content-Type: application/pdf" \
  --data-binary "@../../../labs/lab-3-document-processing/samples/sample-invoice.pdf" | jq
```

You get a JSON `DocumentProcessingResult` with a `status` of `AutoApproved` or
`PendingReview`, the extracted `fields`, and human-readable `reasons`.

### 7. Exercise the routing gate

Lower `DocumentProcessing:ConfidenceThreshold` to `0.50` and re-run — the document
auto-approves. Raise it to `0.99` or add a required field that the model won’t find (e.g.
`DocumentProcessing:RequiredFields:0=PurchaseOrder`) and re-run — it routes to
**PendingReview** and writes a message to the `document-review` queue. The
`ReviewQueueFunction` logs the reviewer notification (the human-in-the-loop stub).

> 📋 **Evidence awareness:** the specialization expects proof that a human approves
> low-confidence automation outcomes. An assessor would capture the queued review item plus
> the reviewer’s decision (approve/reject) and timestamp. This lab builds the **routing and
> queue**; wiring a real approval UI (Logic App, Teams, or a small web app) and capturing the
> decision trail is the evidence step — don’t build evidence tooling here.

### 8. (Optional) Enable modular-inference insights

Turn on LLM post-processing (summary + category) — it runs on the **free GitHub Models**
provider by default:

In `local.settings.json` set:

```json
"DocumentProcessing:EnableInsights": "true",
"INFERENCE_PROVIDER": "github",
"GITHUB_TOKEN": "<your-pat-with-models-read>",
"GITHUB_MODELS_MODEL": "openai/gpt-4o-mini"
```

Re-run Step 6 — the result now includes an `insights` object. Switch providers **without
touching code**:

| Provider | Set `INFERENCE_PROVIDER` | Plus |
| --- | --- | --- |
| GitHub Models (free) | `github` | `GITHUB_TOKEN`, `GITHUB_MODELS_MODEL` |
| Azure OpenAI | `azure_openai` | `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_DEPLOYMENT` (key optional → Entra) |
| Azure AI Foundry | `foundry` | `AZURE_AI_FOUNDRY_ENDPOINT`, `AZURE_AI_FOUNDRY_MODEL` (key optional → Entra) |

The feature code only ever calls `IChatClient` — the provider is a configuration choice.

### 9. Provision Azure infrastructure (Bicep)

```bash
cd ../../../infra/bicep/doc-intelligence
az group create -n rg-lab3-doc -l swedencentral
az deployment group create -g rg-lab3-doc -f main.bicep -p main.bicepparam
```

This creates the storage account (keys disabled), Document Intelligence (local auth
disabled), the Flex Consumption Function App, workspace-based Application Insights, a
user-assigned managed identity, and scoped role assignments. See
[`infra/bicep/doc-intelligence/README.md`](../../infra/bicep/doc-intelligence/README.md)
for parameters and the identity model.

### 10. Deploy the Functions app

```bash
cd ../../../src/document-processing/IAuto.DocumentProcessing.Functions
func azure functionapp publish <functionAppName>   # from the Bicep outputs
```

App settings (endpoints, identity client ID, queue URIs) were set by Bicep — no secrets to
copy.

### 11. Wire the blob trigger (Event Grid)

Flex Consumption requires the **Event Grid** blob-trigger source. After the code is
deployed, create the Event Grid subscription from the storage account to the blob-extension
endpoint — the exact commands are in the
[infra README](../../infra/bicep/doc-intelligence/README.md#wire-the-blob-trigger-event-grid--post-deploy).

### 12. End-to-end test on Azure

Upload the sample to the input container and watch it flow:

```bash
az storage blob upload \
  --account-name <storageAccountName> --auth-mode login \
  -c incoming-documents -f ../../../labs/lab-3-document-processing/samples/sample-invoice.pdf \
  -n sample-invoice.pdf
```

Confirm in the Azure portal: the blob trigger ran, a review message appears in
`document-review` (if it routed for review), and traces/metrics land in Application
Insights.

---

## Validation

Run from `src/document-processing` (use the `W:` short path on Windows if needed):

```bash
# 0 warnings / 0 errors
dotnet build IAuto.DocumentProcessing.slnx -c Release

# style is clean
dotnet format IAuto.DocumentProcessing.slnx --verify-no-changes

# every component is covered, no network
dotnet test IAuto.DocumentProcessing.slnx -c Release

# no known vulnerabilities (including transitive)
dotnet list IAuto.DocumentProcessing.slnx package --vulnerable --include-transitive
```

```bash
# infrastructure compiles with no warnings
az bicep build --file infra/bicep/doc-intelligence/main.bicep --stdout > $null
```

You are done when all four .NET checks are green, Bicep builds clean, and (optionally) the
end-to-end Azure test shows a processed document and a telemetry trace.

---

## Paid-tier upgrade path

This lab defaults to **free / consumption** tiers. Upgrade when you need more:

- **Document Intelligence**: the resource has no free SKU; `S0` is consumption-priced.
  Move from `prebuilt-invoice` to a **custom model** (train on your own layouts) when prebuilt
  fields don’t fit — see Document Intelligence Studio. Higher throughput → request a TPS quota
  increase.
- **Inference**: GitHub Models is rate-limited and free. For production SLAs and data
  residency, switch `INFERENCE_PROVIDER` to **Azure OpenAI** or **Azure AI Foundry** (no code
  change) and grant the managed identity **Cognitive Services OpenAI User**.
- **Functions**: Flex Consumption scales to zero. For predictable latency, configure
  **always-ready instances** (`scaleAndConcurrency.alwaysReady`) or move to a dedicated plan.
- **Storage / observability**: Standard LRS and a 30-day Log Analytics retention are dev
  defaults — raise retention and consider ZRS/GRS for resilience.

---

## 📋 Evidence awareness (summary)

The specialization assessor would expect, for a migrated automation:

- The **review/approval trail** for low-confidence documents (Step 7).
- Proof the workload is **secure-by-default** on Azure — `allowSharedKeyAccess=false`,
  `disableLocalAuth=true`, identity-scoped RBAC, and the deployment outputs (Step 9).
- A **telemetry trace** of a processed document in Application Insights (Step 12).

This lab teaches you to *produce* each of these. Capturing the screenshots/exports is the
evidence step — we deliberately do **not** build evidence-collection tooling.

---

## Trainer notes

- **Timing (~80 min):** intro + source-flow framing 10 · Steps 1–5 (build/test) 20 ·
  Step 6–7 (run + routing) 20 · Step 8 (insights/providers) 10 · Steps 9–12 (Azure) 20.
  If the room has no Azure subscriptions, stop after Step 8 — Steps 9–12 become a demo.
- **Talking points:** (1) unattended RPA = an *event* + *AI extraction* + *exception path*;
  Azure expresses each as a first-class primitive. (2) The provider-agnostic `IChatClient`
  is the reusable migration pattern — show switching providers live by editing one setting.
  (3) Entra ID over keys: contrast `allowSharedKeyAccess=false` with the old connection-string
  habit.
- **Common pitfalls:** forgetting to start **Azurite** before `func start`; **MSB3030** on
  deep Windows clones (use the long-path fix / `subst W:`); pasting a `GITHUB_TOKEN` without
  `models: read`; expecting the blob trigger to fire on Flex Consumption **without** the
  Event Grid subscription (Step 11).
- **Reset between runs:** delete `local.settings.json` edits or re-copy the example; clear the
  `document-review` queue and `incoming-documents` container; `az group delete -n rg-lab3-doc
  --yes --no-wait` to tear down Azure.
- **Solutions:** a completed reference lives on the `solutions` branch.
