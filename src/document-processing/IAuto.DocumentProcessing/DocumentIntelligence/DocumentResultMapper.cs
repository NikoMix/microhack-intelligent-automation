using System.Globalization;
using Azure.AI.DocumentIntelligence;
using IAuto.DocumentProcessing.Models;

namespace IAuto.DocumentProcessing.DocumentIntelligence;

/// <summary>
/// Maps an Azure AI Document Intelligence <see cref="AnalyzeResult"/> into the pipeline's
/// provider-neutral <see cref="DocumentExtractionResult"/>. Kept pure and free of SDK clients
/// so it can be unit tested with <c>DocumentIntelligenceModelFactory</c> (no network).
/// </summary>
internal static class DocumentResultMapper
{
    /// <summary>Map an analyze result for the given model into an extraction result.</summary>
    /// <param name="modelId">Model id that produced the result.</param>
    /// <param name="result">The raw analyze result.</param>
    /// <returns>The mapped extraction result.</returns>
    public static DocumentExtractionResult Map(string modelId, AnalyzeResult result)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(modelId);
        ArgumentNullException.ThrowIfNull(result);

        var fields = new List<ExtractedField>();
        double? documentConfidence = null;

        if (result.Documents is { Count: > 0 })
        {
            foreach (AnalyzedDocument document in result.Documents)
            {
                double docConfidence = document.Confidence;
                documentConfidence = documentConfidence is null
                    ? docConfidence
                    : Math.Min(documentConfidence.Value, docConfidence);

                foreach (KeyValuePair<string, DocumentField> pair in document.Fields)
                {
                    DocumentField field = pair.Value;
                    fields.Add(new ExtractedField(
                        pair.Key,
                        FieldToString(field),
                        field.Confidence,
                        field.FieldType.ToString()));
                }
            }
        }

        double? overall = documentConfidence ?? MinFieldConfidence(fields);

        return new DocumentExtractionResult
        {
            ModelId = modelId,
            Fields = fields,
            Content = result.Content ?? string.Empty,
            PageCount = result.Pages?.Count ?? 0,
            OverallConfidence = overall,
        };
    }

    private static double? MinFieldConfidence(IReadOnlyList<ExtractedField> fields)
    {
        double? min = null;
        foreach (ExtractedField field in fields)
        {
            if (field.Confidence is { } confidence)
            {
                min = min is null ? confidence : Math.Min(min.Value, confidence);
            }
        }

        return min;
    }

    private static string? FieldToString(DocumentField field)
    {
        DocumentFieldType type = field.FieldType;
        if (type == DocumentFieldType.String)
        {
            return field.ValueString;
        }

        if (type == DocumentFieldType.Currency)
        {
            return FormatCurrency(field.ValueCurrency);
        }

        if (type == DocumentFieldType.Double)
        {
            return field.ValueDouble?.ToString(CultureInfo.InvariantCulture);
        }

        if (type == DocumentFieldType.Int64)
        {
            return field.ValueInt64?.ToString(CultureInfo.InvariantCulture);
        }

        if (type == DocumentFieldType.Date)
        {
            return field.ValueDate?.ToString("O", CultureInfo.InvariantCulture);
        }

        return field.Content;
    }

    private static string FormatCurrency(CurrencyValue currency)
    {
        string symbol = currency.CurrencySymbol ?? currency.CurrencyCode ?? string.Empty;
        return symbol + currency.Amount.ToString(CultureInfo.InvariantCulture);
    }
}
