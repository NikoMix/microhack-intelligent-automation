using IAuto.DocumentProcessing.Abstractions;
using IAuto.DocumentProcessing.Models;

namespace IAuto.DocumentProcessing.Tests.Fakes;

/// <summary>In-memory <see cref="IDocumentAnalyzer"/> returning a configured result or fault.</summary>
internal sealed class FakeDocumentAnalyzer : IDocumentAnalyzer
{
    public DocumentExtractionResult? Result { get; set; }

    public Exception? Exception { get; set; }

    public int CallCount { get; private set; }

    public Task<DocumentExtractionResult> AnalyzeAsync(
        DocumentAnalysisRequest request,
        CancellationToken cancellationToken = default)
    {
        CallCount++;
        if (Exception is not null)
        {
            return Task.FromException<DocumentExtractionResult>(Exception);
        }

        return Task.FromResult(
            Result ?? throw new InvalidOperationException("FakeDocumentAnalyzer.Result was not set."));
    }
}
