using IAuto.DocumentProcessing.Models;

namespace IAuto.DocumentProcessing.HumanInTheLoop;

/// <summary>Result of evaluating a document for human review.</summary>
/// <param name="Status">Routing status (auto-approved or pending review).</param>
/// <param name="Reasons">Reasons explaining the decision; empty when auto-approved.</param>
public sealed record ReviewDecision(DocumentProcessingStatus Status, IReadOnlyList<string> Reasons);
