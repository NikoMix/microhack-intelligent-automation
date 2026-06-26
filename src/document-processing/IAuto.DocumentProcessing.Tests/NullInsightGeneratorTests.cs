using IAuto.DocumentProcessing.Insights;
using IAuto.DocumentProcessing.Models;

namespace IAuto.DocumentProcessing.Tests;

/// <summary>Tests the no-op insight generator used when LLM post-processing is disabled.</summary>
public sealed class NullInsightGeneratorTests
{
    [Fact]
    public async Task GenerateAsync_ReturnsNull()
    {
        var generator = new NullInsightGenerator();

        DocumentInsights? insights = await generator.GenerateAsync(
            new DocumentExtractionResult { ModelId = "prebuilt-invoice" });

        Assert.Null(insights);
    }
}
