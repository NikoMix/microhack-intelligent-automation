# .NET — scaffold a modular-inference capability

Target: **net10.0**. Reuse the shared `IAuto.Inference` library, which unifies all three
providers on `Microsoft.Extensions.AI`'s `IChatClient`. Never reference a provider SDK directly
in feature code.

## 1. Reference the shared project

```xml
<ItemGroup>
  <ProjectReference Include="..\inference\dotnet\IAuto.Inference\IAuto.Inference.csproj" />
</ItemGroup>
```

## 2. Depend on `IChatClient`, not a provider

Inject `IChatClient` so the capability is testable with a stub. Build the concrete client at the
edge with `ChatClientFactory.CreateFromEnvironment()` (or register it via DI).

```csharp
using IAuto.Inference;
using Microsoft.Extensions.AI;

public sealed class Classifier(IChatClient client)
{
    private const string System = "You are a precise assistant. Never invent facts.";

    public Task<string> ClassifyAsync(string text, CancellationToken ct = default) =>
        client.CompleteTextAsync($"Classify:\n{text}", System, ct);
}

// At the composition root only:
IChatClient client = ChatClientFactory.CreateFromEnvironment();
var classifier = new Classifier(client);
```

`CompleteTextAsync` is the shared ergonomic helper over `IChatClient.GetResponseAsync`. Switching
providers is a configuration change (`INFERENCE_PROVIDER`), never a code change.

## 3. Test with a stub — no network, no provider

Implement a tiny in-memory `IChatClient` that records the last messages and returns a canned
reply; assert on both. See `src/inference/dotnet/IAuto.Inference.Tests/StubChatClient.cs` for a
complete, copyable stub.

```csharp
var stub = new StubChatClient { Reply = "invoice" };
var result = await new Classifier(stub).ClassifyAsync("Pay $10 to Contoso");
Assert.Equal("invoice", result);
Assert.NotNull(stub.LastMessages);
```

## 4. Configuration & gates

- Configure through the shared env contract; prefer Entra ID (`DefaultAzureCredential`) by leaving
  `*_API_KEY` blank. Add new keys to `.env.example` only.
- Keep analyzers and docs clean: `EnforceCodeStyleInBuild`, `TreatWarningsAsErrors`, XML docs,
  `dotnet format --verify-no-changes`, `dotnet test`, and `dotnet list package --vulnerable`
  (NuGetAudit) — all green.
