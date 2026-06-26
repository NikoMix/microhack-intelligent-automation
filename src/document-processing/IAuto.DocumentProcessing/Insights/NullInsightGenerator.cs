using IAuto.DocumentProcessing.Abstractions;
using IAuto.DocumentProcessing.Models;

namespace IAuto.DocumentProcessing.Insights;

/// <summary>No-op insight generator used when LLM post-processing is disabled.</summary>
public sealed class NullInsightGenerator : IDocumentInsightGenerator
{
    /// <inheritdoc />
    public Task<DocumentInsights?> GenerateAsync(
        DocumentExtractionResult extraction,
        CancellationToken cancellationToken = default) =>
        Task.FromResult<DocumentInsights?>(null);
}
