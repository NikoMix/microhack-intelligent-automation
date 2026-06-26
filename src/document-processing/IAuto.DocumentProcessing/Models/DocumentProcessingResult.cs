namespace IAuto.DocumentProcessing.Models;

/// <summary>Final result of running a document through the processing pipeline.</summary>
public sealed record DocumentProcessingResult
{
    /// <summary>Logical name of the processed document.</summary>
    public required string DocumentName { get; init; }

    /// <summary>Routing outcome for the document.</summary>
    public required DocumentProcessingStatus Status { get; init; }

    /// <summary>Structured extraction result, when analysis succeeded.</summary>
    public DocumentExtractionResult? Extraction { get; init; }

    /// <summary>Optional LLM insights, when enabled and analysis succeeded.</summary>
    public DocumentInsights? Insights { get; init; }

    /// <summary>Human-readable reasons that explain the routing decision.</summary>
    public IReadOnlyList<string> Reasons { get; init; } = [];

    /// <summary>Identifier of the queued approval message when routed for review.</summary>
    public string? ApprovalReference { get; init; }

    /// <summary>Create a failed result with an explanatory reason.</summary>
    /// <param name="documentName">Logical name of the document.</param>
    /// <param name="reason">Why processing failed.</param>
    /// <returns>A <see cref="DocumentProcessingResult"/> in the failed state.</returns>
    public static DocumentProcessingResult Failed(string documentName, string reason) =>
        new()
        {
            DocumentName = documentName,
            Status = DocumentProcessingStatus.Failed,
            Reasons = [reason],
        };
}
