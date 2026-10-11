# IAuto.Inference (.NET)

Modular, provider-agnostic chat inference for .NET — the C# twin of the Python
`iauto-inference` package. One abstraction (`Microsoft.Extensions.AI.IChatClient`)
over three backends, swapped by configuration only:

| Provider | `INFERENCE_PROVIDER` | Auth | Notes |
|---|---|---|---|
| **GitHub Models** | `github` (default) | `GITHUB_TOKEN` | Free, great for class delivery |
| **Azure OpenAI** | `azure_openai` | API key **or** Entra ID | Production migration target |
| **Azure AI Foundry** | `foundry` | API key **or** Entra ID | Foundry model catalog |

All three are unified on the OpenAI SDK and surfaced through `IChatClient`, so your
agents, RAG pipelines, and tools never depend on a specific backend. Migrating from
GitHub Models (lab) to Azure OpenAI (production) is a configuration change, not a
code change.

## Why this exists (course context)

This package backs **Lab 2** of the *From Power Platform to Azure* training and is a
dependency for the document-processing (.NET) labs. It demonstrates the
**modular inference** requirement: build once, run on free models in class, then
flip to Azure for production — no rewrite.

## Install / reference

```xml
<ProjectReference Include="..\..\inference\dotnet\IAuto.Inference\IAuto.Inference.csproj" />
```

## Usage

### Direct factory

```csharp
using IAuto.Inference;

// Reads INFERENCE_PROVIDER + provider env vars.
IChatClient client = ChatClientFactory.CreateFromEnvironment();

string answer = await client.CompleteTextAsync(
    "Summarise the benefits of migrating RPA to Azure in one sentence.");
Console.WriteLine(answer);
```

### Dependency injection

```csharp
using IAuto.Inference;
using Microsoft.Extensions.DependencyInjection;

var services = new ServiceCollection();
services.AddModularInference();           // from environment
// or: services.AddModularInference(o => { o.Provider = Provider.AzureOpenAI; ... });

using var provider = services.BuildServiceProvider();
var client = provider.GetRequiredService<IChatClient>();
```

Because it's an `IChatClient`, you can hand it straight to **Microsoft Agent
Framework** (`Microsoft.Agents.AI`) for the agent and MCP labs.

## Configuration

Copy `.env.example` and set the variables for your chosen provider, or export them in
your shell / CI. See the table above; the full contract is shared verbatim with the
Python package so both languages behave identically.

## Quality gates

This project treats warnings as errors and enables Roslyn analyzers, code-style
enforcement, XML docs, and NuGet supply-chain auditing:

```powershell
dotnet build  -c Release   # analyzers + style + warnings-as-errors
dotnet test   -c Release   # xUnit suite
dotnet format --verify-no-changes   # style verification (CI)
```

> 📋 **Evidence awareness:** In the specialization, you would capture build/test
> output and dependency-audit results as evidence of engineering rigor. We skip the
> capture step here, but the gates above are exactly what you would screenshot.
