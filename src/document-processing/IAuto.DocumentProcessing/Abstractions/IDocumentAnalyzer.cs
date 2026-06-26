using IAuto.DocumentProcessing.Models;

namespace IAuto.DocumentProcessing.Abstractions;

/// <summary>Analyzes documents with Azure AI Document Intelligence.</summary>
public interface IDocumentAnalyzer
{
    /// <summary>Analyze a document and return its structured extraction result.</summary>
    /// <param name="request">The document to analyze.</param>
    /// <param name="cancellationToken">Token to cancel the operation.</param>
    /// <returns>The structured extraction result.</returns>
    Task<DocumentExtractionResult> AnalyzeAsync(
        DocumentAnalysisRequest request,
        CancellationToken cancellationToken = default);
}
