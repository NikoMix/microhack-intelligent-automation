using IAuto.DocumentProcessing.Abstractions;
using IAuto.DocumentProcessing.Models;

namespace IAuto.DocumentProcessing.Tests.Fakes;

/// <summary><see cref="IDocumentInsightGenerator"/> returning a configured value and counting calls.</summary>
internal sealed class FakeInsightGenerator : IDocumentInsightGenerator
{
    public DocumentInsights? Insights { get; set; }

    public int CallCount { get; private set; }

    public Task<DocumentInsights?> GenerateAsync(
        DocumentExtractionResult extraction,
        CancellationToken cancellationToken = default)
    {
        CallCount++;
        return Task.FromResult(Insights);
    }
}
