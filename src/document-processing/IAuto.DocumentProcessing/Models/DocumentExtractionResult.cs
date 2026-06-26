namespace IAuto.DocumentProcessing.Models;

/// <summary>Structured result of analyzing a document with a Document Intelligence model.</summary>
public sealed record DocumentExtractionResult
{
    /// <summary>Document Intelligence model id used for analysis (for example <c>prebuilt-invoice</c>).</summary>
    public required string ModelId { get; init; }

    /// <summary>Fields extracted from the document. Empty for layout-only models.</summary>
    public IReadOnlyList<ExtractedField> Fields { get; init; } = [];

    /// <summary>Full text content recognised in the document.</summary>
    public string Content { get; init; } = string.Empty;

    /// <summary>Number of pages processed.</summary>
    public int PageCount { get; init; }

    /// <summary>
    /// Overall confidence signal (0–1) used for routing. Prefers the document-level
    /// confidence; <see langword="null"/> when the model reports none (which routes to review).
    /// </summary>
    public double? OverallConfidence { get; init; }
}
