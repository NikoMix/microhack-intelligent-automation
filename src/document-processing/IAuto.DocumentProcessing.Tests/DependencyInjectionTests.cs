using IAuto.DocumentProcessing.Abstractions;
using IAuto.DocumentProcessing.DependencyInjection;
using IAuto.DocumentProcessing.Insights;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;

namespace IAuto.DocumentProcessing.Tests;

/// <summary>Tests the composition root wiring without contacting any Azure service.</summary>
public sealed class DependencyInjectionTests
{
    private static IConfiguration BuildConfig(bool enableInsights) =>
        new ConfigurationBuilder()
            .AddInMemoryCollection(new Dictionary<string, string?>
            {
                ["DocumentIntelligence:Endpoint"] = "https://example.cognitiveservices.azure.com/",
                ["DocumentIntelligence:ApiKey"] = "test-key",
                ["Approval:ConnectionString"] = "UseDevelopmentStorage=true",
                ["DocumentProcessing:EnableInsights"] = enableInsights ? "true" : "false",
            })
            .Build();

    [Fact]
    public void AddDocumentProcessing_ResolvesPipeline_WhenInsightsDisabled()
    {
        var services = new ServiceCollection();
        services.AddLogging();
        services.AddDocumentProcessing(BuildConfig(enableInsights: false));

        using ServiceProvider provider = services.BuildServiceProvider();

        Assert.NotNull(provider.GetRequiredService<IDocumentProcessingPipeline>());
        Assert.IsType<NullInsightGenerator>(provider.GetRequiredService<IDocumentInsightGenerator>());
    }

    [Fact]
    public void AddDocumentProcessing_RegistersChatInsightGenerator_WhenInsightsEnabled()
    {
        // Insights wiring calls AddModularInference, which eagerly validates provider
        // configuration. Pin the free GitHub Models provider with a placeholder token so the
        // composition root resolves without contacting any network endpoint.
        using EnvironmentVariableScope _ = EnvironmentVariableScope.Set(
            new Dictionary<string, string?>(StringComparer.Ordinal)
            {
                ["INFERENCE_PROVIDER"] = "github",
                ["GITHUB_TOKEN"] = "placeholder-token-not-used-for-network",
            });

        var services = new ServiceCollection();
        services.AddLogging();
        services.AddDocumentProcessing(BuildConfig(enableInsights: true));

        ServiceDescriptor descriptor = Assert.Single(
            services,
            d => d.ServiceType == typeof(IDocumentInsightGenerator));
        Assert.Equal(typeof(ChatInsightGenerator), descriptor.ImplementationType);
    }
}
