namespace IAuto.DocumentProcessing.Models;

/// <summary>Optional LLM-generated insights about a processed document.</summary>
/// <param name="Summary">Concise natural-language summary of the document.</param>
/// <param name="Category">Best-fit category label chosen by the model.</param>
/// <param name="Rationale">Short justification for the category, when provided.</param>
public sealed record DocumentInsights(string Summary, string Category, string? Rationale);
