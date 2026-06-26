using IAuto.HybridIntegration.Connector.Services;
using IAuto.Inference;
using Microsoft.Azure.Functions.Worker;
using Microsoft.Azure.Functions.Worker.Builder;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;

var builder = FunctionsApplication.CreateBuilder(args);

// ASP.NET Core integration: HTTP triggers receive HttpRequest and return IActionResult.
builder.ConfigureFunctionsWebApplication();

builder.Services
    .AddApplicationInsightsTelemetryWorkerService()
    .ConfigureFunctionsApplicationInsights();

// Modular inference: the provider (GitHub Models | Azure OpenAI | Azure AI Foundry) is chosen
// by configuration only. The shared layer registers a singleton, provider-agnostic IChatClient
// and validates configuration at startup so misconfiguration fails fast.
builder.Services.AddModularInference();

// Typed client for the on-prem system. Base address and the optional API key come from
// configuration, so the same code targets the local stub in the lab and the real line-of-business
// system (reached over a hybrid connection) in production. The API key is injected from Key Vault
// via a managed-identity-backed app setting when deployed to Azure.
builder.Services.AddHttpClient<IOnPremClient, OnPremClient>(static (provider, client) =>
{
    var configuration = provider.GetRequiredService<IConfiguration>();
    var baseUrl = configuration["ONPREM_BASE_URL"]
        ?? throw new InvalidOperationException(
            "ONPREM_BASE_URL is not configured. Set it to the on-prem system base address.");
    client.BaseAddress = new Uri(baseUrl, UriKind.Absolute);
    client.Timeout = TimeSpan.FromSeconds(30);

    var apiKey = configuration["ONPREM_API_KEY"];
    if (!string.IsNullOrWhiteSpace(apiKey))
    {
        client.DefaultRequestHeaders.Add("x-api-key", apiKey);
    }
});

builder.Services.AddScoped<IOrderEnricher, OrderEnricher>();

builder.Build().Run();
