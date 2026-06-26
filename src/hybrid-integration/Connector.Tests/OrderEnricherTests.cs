using IAuto.HybridIntegration.Connector.Models;
using IAuto.HybridIntegration.Connector.Services;
using IAuto.HybridIntegration.Connector.Tests.Fakes;
using IAuto.Inference;
using Microsoft.Extensions.Logging.Abstractions;

namespace IAuto.HybridIntegration.Connector.Tests;

/// <summary>Unit tests for <see cref="OrderEnricher"/>, the modular-inference capability.</summary>
public sealed class OrderEnricherTests
{
    private static OnPremOrder SampleOrder() => new()
    {
        OrderId = "ORD-1001",
        Customer = "Contoso Retail",
        Status = "Shipped",
        Carrier = "Northwind Freight",
        TrackingNumber = "NF-88421156",
        EstimatedDelivery = new DateOnly(2026, 7, 2),
        LastUpdatedUtc = new DateTimeOffset(2026, 6, 26, 8, 30, 0, TimeSpan.Zero),
    };

    private static OrderEnricher CreateEnricher(
        StubChatClient chat,
        StubOnPremClient onPrem,
        InferenceOptions options) =>
        new(chat, onPrem, options, NullLogger<OrderEnricher>.Instance);

    [Fact]
    public async Task EnrichAsync_WhenOrderFound_ReturnsGroundedAnswer()
    {
        var chat = new StubChatClient { Reply = "Your order shipped via Northwind Freight." };
        var onPrem = new StubOnPremClient { Order = SampleOrder() };
        var enricher = CreateEnricher(chat, onPrem, new InferenceOptions());

        var result = await enricher.EnrichAsync(
            new EnrichmentRequest { OrderId = "ORD-1001", Question = "Where is my order?" });

        Assert.True(result.Found);
        Assert.Equal("ORD-1001", result.OrderId);
        Assert.Equal("Shipped", result.Status);
        Assert.Equal("Your order shipped via Northwind Freight.", result.Answer);
        Assert.Equal("github", result.Provider);
    }

    [Fact]
    public async Task EnrichAsync_WhenOrderFound_PromptIsGroundedInOrderFacts()
    {
        var chat = new StubChatClient();
        var onPrem = new StubOnPremClient { Order = SampleOrder() };
        var enricher = CreateEnricher(chat, onPrem, new InferenceOptions());

        await enricher.EnrichAsync(
            new EnrichmentRequest { OrderId = "ORD-1001", Question = "Where is my order?" });

        Assert.NotNull(chat.LastMessages);
        var system = chat.LastMessages!.Single(m => m.Role == Microsoft.Extensions.AI.ChatRole.System);
        var user = chat.LastMessages!.Single(m => m.Role == Microsoft.Extensions.AI.ChatRole.User);
        Assert.Contains("customer-service", system.Text, StringComparison.OrdinalIgnoreCase);
        Assert.Contains("ORD-1001", user.Text, StringComparison.Ordinal);
        Assert.Contains("Northwind Freight", user.Text, StringComparison.Ordinal);
        Assert.Contains("Where is my order?", user.Text, StringComparison.Ordinal);
    }

    [Fact]
    public async Task EnrichAsync_WhenOrderMissing_SkipsInference()
    {
        var chat = new StubChatClient();
        var onPrem = new StubOnPremClient { Order = null };
        var enricher = CreateEnricher(chat, onPrem, new InferenceOptions());

        var result = await enricher.EnrichAsync(
            new EnrichmentRequest { OrderId = "ORD-9999", Question = "Where is my order?" });

        Assert.False(result.Found);
        Assert.Null(result.Status);
        Assert.Null(result.Model);
        Assert.Contains("ORD-9999", result.Answer, StringComparison.Ordinal);
        Assert.Equal(0, chat.CallCount);
    }

    [Fact]
    public async Task EnrichAsync_TrimsModelAnswer()
    {
        var chat = new StubChatClient { Reply = "   spaced answer   " };
        var onPrem = new StubOnPremClient { Order = SampleOrder() };
        var enricher = CreateEnricher(chat, onPrem, new InferenceOptions());

        var result = await enricher.EnrichAsync(
            new EnrichmentRequest { OrderId = "ORD-1001", Question = "Status?" });

        Assert.Equal("spaced answer", result.Answer);
    }

    [Theory]
    [InlineData("github")]
    [InlineData("azure_openai")]
    [InlineData("foundry")]
    public async Task EnrichAsync_ReportsProviderWireName(string expectedProvider)
    {
        var options = expectedProvider switch
        {
            "github" => new InferenceOptions { Provider = Provider.GitHub },
            "azure_openai" => new InferenceOptions
            {
                Provider = Provider.AzureOpenAI,
                AzureOpenAIDeployment = "gpt-4o",
            },
            _ => new InferenceOptions
            {
                Provider = Provider.Foundry,
                FoundryModel = "phi-4",
            },
        };

        var chat = new StubChatClient { Reply = "ok" };
        var onPrem = new StubOnPremClient { Order = SampleOrder() };
        var enricher = CreateEnricher(chat, onPrem, options);

        var result = await enricher.EnrichAsync(
            new EnrichmentRequest { OrderId = "ORD-1001", Question = "Status?" });

        Assert.Equal(expectedProvider, result.Provider);
        Assert.False(string.IsNullOrWhiteSpace(result.Model));
    }

    [Fact]
    public async Task EnrichAsync_NullRequest_Throws()
    {
        var enricher = CreateEnricher(
            new StubChatClient(),
            new StubOnPremClient { Order = SampleOrder() },
            new InferenceOptions());

        await Assert.ThrowsAsync<ArgumentNullException>(() => enricher.EnrichAsync(null!));
    }
}
