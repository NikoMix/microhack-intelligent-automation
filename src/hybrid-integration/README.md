# Hybrid Integration (`src/hybrid-integration`)

The application tier of **Lab 6** — a hybrid reference pattern that fronts an on-prem
system with Azure managed services and enriches its responses with modular AI inference.

```
APIM (Consumption)  ──►  Logic App Standard  ──►  Connector Function  ──►  on-prem stub
   front door            enrich-order             .NET 10 isolated         ASP.NET Core
                         (workflow.json)          + IAuto.Inference        minimal API
```

A caller asks an order-status question at the APIM gateway. The Logic App workflow forwards
it to the Connector, which looks the order up in the on-prem system and asks the shared
`IAuto.Inference` `IChatClient` to answer **using only those facts**. The provider
(GitHub Models / Azure OpenAI / Azure AI Foundry) is chosen by configuration — no feature
code references a concrete provider.

## Projects

| Path | Project | What it is |
| --- | --- | --- |
| `OnPremStub/` | `IAuto.HybridIntegration.OnPremStub` | ASP.NET Core minimal API standing in for a line-of-business order system (`/health`, `/orders`, `/orders/{id}`). Seeded with `ORD-1001/1002/1003`. |
| `Connector/` | `IAuto.HybridIntegration.Connector` | .NET 10 isolated Function. `POST /api/enrich-order` → on-prem lookup + grounded inference. Consumes `IAuto.Inference`. |
| `Connector.Tests/` | `IAuto.HybridIntegration.Connector.Tests` | xUnit suite (29 tests) using fakes only — no live Azure, no live model. |
| `logic-app/` | — | Logic App Standard project: the stateful `enrich-order` workflow. See its [README](./logic-app/README.md). |
| `HybridIntegration.slnx` | — | Solution that builds the three .NET projects. |

## Build, test, and run

```powershell
# Build + test everything (no Azure, no model calls — fakes cover the AI path)
dotnet test HybridIntegration.slnx -c Release

# Run the on-prem stub (terminal 1)
dotnet run --project OnPremStub        # listens on http://localhost:5179

# Run the Connector (terminal 2) — copy and edit settings first
copy Connector\local.settings.json.example Connector\local.settings.json
func start --script-root Connector     # requires Azure Functions Core Tools
```

`func` is only needed to *run* the Function/Logic App locally; the solution **builds and
tests without it**.

## Configuration

`Connector/local.settings.json.example` and [`.env.example`](./.env.example) document the
full contract. The essentials:

- `ONPREM_BASE_URL` / `ONPREM_API_KEY` — where the on-prem system lives and its key.
- `INFERENCE_PROVIDER` + provider settings — see the shared
  [`IAuto.Inference`](../inference/dotnet) layer. Default is free **GitHub Models**.

In Azure, secrets (`ONPREM_API_KEY`, the provider token) are delivered through **Key Vault
references** resolved by the **user-assigned managed identity** — never stored in plain app
settings. The infrastructure that wires this up lives in
[`infra/bicep/integration`](../../infra/bicep/integration).

## Quality bar

- .NET 10, nullable + analyzers + `TreatWarningsAsErrors`, XML docs, `NuGetAudit`.
- `dotnet format --verify-no-changes --severity error` clean.
- `dotnet list package --vulnerable --include-transitive` → no vulnerable packages.
- Tests are fast and provider-free (fakes); CI runs them on every push/PR.

> 📋 **Evidence awareness:** the specialization expects proof that the on-prem system is
> brokered (never directly exposed) and that AI is provider-portable. An assessor would
> capture the APIM → Logic App → Function → on-prem call chain and a provider switch
> (config-only) producing the same contract. We build the runnable artifact, not the
> evidence tooling.
