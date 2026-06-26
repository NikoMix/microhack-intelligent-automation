using IAuto.DocumentProcessing.Models;

namespace IAuto.DocumentProcessing.Abstractions;

/// <summary>Generates optional LLM insights for an analyzed document via modular inference.</summary>
public interface IDocumentInsightGenerator
{
    /// <summary>Generate insights for an extraction result, or <see langword="null"/> when disabled.</summary>
    /// <param name="extraction">The structured extraction result.</param>
    /// <param name="cancellationToken">Token to cancel the operation.</param>
    /// <returns>The generated insights, or <see langword="null"/> when generation is disabled or fails.</returns>
    Task<DocumentInsights?> GenerateAsync(
        DocumentExtractionResult extraction,
        CancellationToken cancellationToken = default);
}
