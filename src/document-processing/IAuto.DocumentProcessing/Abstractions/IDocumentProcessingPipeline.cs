using IAuto.DocumentProcessing.Models;

namespace IAuto.DocumentProcessing.Abstractions;

/// <summary>Orchestrates analysis, optional insights, and human-in-the-loop routing.</summary>
public interface IDocumentProcessingPipeline
{
    /// <summary>Process a document end to end and return the routing result.</summary>
    /// <param name="request">The document to process.</param>
    /// <param name="cancellationToken">Token to cancel the operation.</param>
    /// <returns>The final processing result.</returns>
    Task<DocumentProcessingResult> ProcessAsync(
        DocumentAnalysisRequest request,
        CancellationToken cancellationToken = default);
}
