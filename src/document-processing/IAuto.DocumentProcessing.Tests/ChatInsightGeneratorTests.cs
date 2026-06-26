using IAuto.DocumentProcessing.Insights;
using IAuto.DocumentProcessing.Models;
using IAuto.DocumentProcessing.Pipeline;
using IAuto.DocumentProcessing.Tests.Fakes;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.Extensions.Options;

namespace IAuto.DocumentProcessing.Tests;

/// <summary>
/// Tests the modular-inference insight generator's prompt-response parsing using a stub
/// <c>IChatClient</c>; provider selection is configuration-driven and never exercised here.
/// </summary>
public sealed class ChatInsightGeneratorTests
{
    private static ChatInsightGenerator Create(StubChatClient client) =>
        new(client, Options.Create(new DocumentProcessingOptions()), NullLogger<ChatInsightGenerator>.Instance);

    private static DocumentExtractionResult Extraction() =>
        new()
        {
            ModelId = "prebuilt-invoice",
            Content = "Invoice text",
            Fields = [new ExtractedField("VendorName", "ACME", 0.9, "String")],
        };

    [Fact]
    public async Task GenerateAsync_ParsesStrictJson()
    {
        var client = new StubChatClient
        {
            Reply = """{"summary":"An ACME invoice","category":"Invoice","rationale":"Has totals"}""",
        };

        DocumentInsights? insights = await Create(client).GenerateAsync(Extraction());

        Assert.NotNull(insights);
        Assert.Equal("An ACME invoice", insights!.Summary);
        Assert.Equal("Invoice", insights.Category);
        Assert.Equal("Has totals", insights.Rationale);
    }

    [Fact]
    public async Task GenerateAsync_ExtractsJson_FromSurroundingProse()
    {
        var client = new StubChatClient
        {
            Reply = "Here you go:\n{\"summary\":\"S\",\"category\":\"Receipt\"}\nThanks!",
        };

        DocumentInsights? insights = await Create(client).GenerateAsync(Extraction());

        Assert.NotNull(insights);
        Assert.Equal("Receipt", insights!.Category);
    }

    [Fact]
    public async Task GenerateAsync_DefaultsCategory_WhenMissing()
    {
        var client = new StubChatClient { Reply = """{"summary":"S"}""" };

        DocumentInsights? insights = await Create(client).GenerateAsync(Extraction());

        Assert.NotNull(insights);
        Assert.Equal("Other", insights!.Category);
    }

    [Fact]
    public async Task GenerateAsync_ReturnsNull_WhenSummaryMissing()
    {
        var client = new StubChatClient { Reply = """{"category":"Invoice"}""" };

        Assert.Null(await Create(client).GenerateAsync(Extraction()));
    }

    [Fact]
    public async Task GenerateAsync_ReturnsNull_WhenResponseHasNoJson()
    {
        var client = new StubChatClient { Reply = "I cannot help with that." };

        Assert.Null(await Create(client).GenerateAsync(Extraction()));
    }

    [Fact]
    public async Task GenerateAsync_ReturnsNull_WhenChatClientThrows()
    {
        var client = new StubChatClient { ThrowOnCall = true };

        Assert.Null(await Create(client).GenerateAsync(Extraction()));
    }
}
