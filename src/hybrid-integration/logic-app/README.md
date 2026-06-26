# Logic App Standard — `enrich-order` workflow

This is the **integration tier** of the hybrid reference architecture:

```
APIM (Consumption)  ──►  Logic App Standard  ──►  Function connector  ──►  on-prem stub
                          (this folder)           (../Connector)          (../OnPremStub)
```

The `enrich-order` workflow is a **stateful** workflow that accepts an order-status
request over HTTP, calls the .NET isolated **Connector** function (which performs the
modular-inference enrichment), and returns the enriched answer to the caller. APIM sits
in front of this workflow so the on-prem system is never exposed directly.

## Files

| File | Purpose |
| --- | --- |
| `enrich-order/workflow.json` | Stateful workflow: Request trigger → HTTP action → Response (with an upstream-failure branch). |
| `host.json` | Pins the Workflows extension bundle (`Microsoft.Azure.Functions.ExtensionBundle.Workflows`). |
| `connections.json` | Connection references (none required — the workflow calls the Function over plain HTTP). |
| `local.settings.json.example` | Template for local app settings. Copy to `local.settings.json` (gitignored). |

## App settings (resolved with `@appsetting(...)`)

| Setting | Meaning | Set by |
| --- | --- | --- |
| `FUNCTION_ENRICH_ORDER_URL` | Absolute URL of the Connector's `enrich-order` endpoint. | Bicep (`infra/bicep/integration`) at deploy time. |
| `FUNCTION_HOST_KEY` | Function host key, sent as the `x-functions-key` header. | Bicep via `listKeys` (or a Key Vault reference). |

> 📋 **Evidence awareness:** the specialization expects proof that the integration tier
> brokers access to the on-prem system (no direct exposure) and that secrets flow through
> managed identity / Key Vault rather than being embedded. An assessor would capture the
> workflow run history, the APIM → Logic App → Function call chain, and the app-setting
> Key Vault references — all of which this lab provisions. We do **not** build evidence
> tooling here.

## Run locally

Logic Apps Standard needs the **Azure Functions Core Tools** plus the Logic Apps extension.
With the Connector running on `http://localhost:7071`:

```bash
cp local.settings.json.example local.settings.json   # then start the host
func start
```

`func` is not required to build or test the rest of this lab — the .NET solution
(`HybridIntegration.slnx`) builds and tests without it.
