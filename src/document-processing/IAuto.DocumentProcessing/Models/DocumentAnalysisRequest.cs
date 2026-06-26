namespace IAuto.DocumentProcessing.Models;

/// <summary>A request to analyze a single document.</summary>
/// <param name="DocumentName">Logical name of the document (for example a blob name).</param>
/// <param name="Content">Raw document bytes.</param>
/// <param name="ContentType">MIME type, when known.</param>
/// <param name="ModelId">Override model id; falls back to the configured default when <see langword="null"/>.</param>
public sealed record DocumentAnalysisRequest(
    string DocumentName,
    BinaryData Content,
    string? ContentType = null,
    string? ModelId = null);
