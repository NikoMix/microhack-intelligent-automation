using System.Globalization;
using IAuto.DocumentProcessing.Models;
using IAuto.DocumentProcessing.Pipeline;

namespace IAuto.DocumentProcessing.HumanInTheLoop;

/// <summary>Pure routing logic deciding whether a document can be auto-approved.</summary>
public static class ReviewRouting
{
    /// <summary>
    /// Evaluate an extraction against the configured confidence threshold and required
    /// fields. Returns the routing status plus human-readable reasons.
    /// </summary>
    /// <param name="extraction">The structured extraction result.</param>
    /// <param name="options">Routing options (threshold and required fields).</param>
    /// <returns>The routing decision.</returns>
    public static ReviewDecision Evaluate(
        DocumentExtractionResult extraction,
        DocumentProcessingOptions options)
    {
        ArgumentNullException.ThrowIfNull(extraction);
        ArgumentNullException.ThrowIfNull(options);

        var reasons = new List<string>();

        if (extraction.OverallConfidence is null)
        {
            reasons.Add("No overall confidence was reported by the model.");
        }
        else if (extraction.OverallConfidence < options.ConfidenceThreshold)
        {
            reasons.Add(string.Create(
                CultureInfo.InvariantCulture,
                $"Overall confidence {extraction.OverallConfidence:P0} is below the {options.ConfidenceThreshold:P0} threshold."));
        }

        foreach (string required in options.RequiredFields)
        {
            if (!HasField(extraction, required))
            {
                reasons.Add($"Required field '{required}' is missing or empty.");
            }
        }

        DocumentProcessingStatus status = reasons.Count == 0
            ? DocumentProcessingStatus.AutoApproved
            : DocumentProcessingStatus.PendingReview;
        return new ReviewDecision(status, reasons);
    }

    private static bool HasField(DocumentExtractionResult extraction, string fieldName)
    {
        foreach (ExtractedField field in extraction.Fields)
        {
            if (string.Equals(field.Name, fieldName, StringComparison.OrdinalIgnoreCase))
            {
                return !string.IsNullOrWhiteSpace(field.Value);
            }
        }

        return false;
    }
}
