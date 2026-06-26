namespace IAuto.DocumentProcessing.Models;

/// <summary>Payload describing a document that needs human review.</summary>
public sealed record ApprovalRequest
{
    /// <summary>Logical name of the document awaiting review.</summary>
    public required string DocumentName { get; init; }

    /// <summary>Model id used to analyze the document.</summary>
    public required string ModelId { get; init; }

    /// <summary>Overall confidence that triggered review, when available.</summary>
    public double? OverallConfidence { get; init; }

    /// <summary>Reasons the document was routed for review.</summary>
    public IReadOnlyList<string> Reasons { get; init; } = [];

    /// <summary>Fields extracted from the document for the reviewer's context.</summary>
    public IReadOnlyList<ExtractedField> Fields { get; init; } = [];

    /// <summary>Optional insights to assist the reviewer.</summary>
    public DocumentInsights? Insights { get; init; }
}
