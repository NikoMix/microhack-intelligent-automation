namespace IAuto.DocumentProcessing.Models;

/// <summary>A single field extracted from a document by Azure AI Document Intelligence.</summary>
/// <param name="Name">Field name (for example <c>InvoiceTotal</c>).</param>
/// <param name="Value">Normalised string value, or <see langword="null"/> when not present.</param>
/// <param name="Confidence">Model confidence in the range 0–1, when reported.</param>
/// <param name="FieldType">Document Intelligence field type (for example <c>String</c> or <c>Currency</c>).</param>
public sealed record ExtractedField(string Name, string? Value, double? Confidence, string FieldType);
