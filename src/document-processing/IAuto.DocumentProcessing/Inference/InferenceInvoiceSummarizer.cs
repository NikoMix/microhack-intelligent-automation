using System.Text.Json;
using IAuto.DocumentProcessing.Models;

namespace IAuto.DocumentProcessing.Inference;

public sealed class InferenceInvoiceSummarizer : IInvoiceSummarizer
{
    private const string SystemPrompt = "You classify inbound supplier invoices for an Azure intelligent automation workflow. Return only compact JSON.";
    private static readonly JsonSerializerOptions JsonOptions = new(JsonSerializerDefaults.Web);
    private readonly IInvoiceSummaryInference _inference;

    public InferenceInvoiceSummarizer(IInvoiceSummaryInference inference)
    {
        _inference = inference ?? throw new ArgumentNullException(nameof(inference));
    }

    public async Task<InvoiceSummaryResult> SummarizeAsync(InvoiceAnalysis invoice, CancellationToken cancellationToken)
    {
        ArgumentNullException.ThrowIfNull(invoice);

        var prompt = BuildPrompt(invoice);
        var response = await _inference.CompleteAsync(SystemPrompt, prompt, cancellationToken).ConfigureAwait(false);
        return ParseResponse(response);
    }

    private static string BuildPrompt(InvoiceAnalysis invoice)
    {
        var payload = JsonSerializer.Serialize(new
        {
            vendor = invoice.VendorName,
            invoiceId = invoice.InvoiceId,
            invoiceDate = invoice.InvoiceDate?.ToString("O"),
            currency = invoice.CurrencyCode,
            total = invoice.Total,
            lineItems = invoice.LineItems.Select(item => new
            {
                item.Description,
                item.Quantity,
                item.UnitPrice,
                item.Amount,
            }),
        }, JsonOptions);

        return "Summarize this prebuilt-invoice extraction in one sentence and classify it. " +
            "Use category standard, high_value, missing_fields, tax_review, or duplicate_review; " +
            "risk low, medium, or high. Return JSON with summary, category, risk, rationale. Invoice: " + payload;
    }

    private static InvoiceSummaryResult ParseResponse(string response)
    {
        if (string.IsNullOrWhiteSpace(response))
        {
            return Fallback(response, "The inference provider returned an empty response.");
        }

        var trimmed = response.Trim();
        var start = trimmed.IndexOf('{', StringComparison.Ordinal);
        var end = trimmed.LastIndexOf('}');
        if (start >= 0 && end > start)
        {
            trimmed = trimmed[start..(end + 1)];
        }

        try
        {
            var parsed = JsonSerializer.Deserialize<InferenceResponse>(trimmed, JsonOptions);
            if (parsed is not null && !string.IsNullOrWhiteSpace(parsed.Summary))
            {
                return new InvoiceSummaryResult(
                    parsed.Summary.Trim(),
                    new InvoiceClassification(
                        Normalize(parsed.Category, "standard"),
                        Normalize(parsed.Risk, "medium"),
                        Normalize(parsed.Rationale, "Model did not provide a rationale.")),
                    response);
            }
        }
        catch (JsonException)
        {
            return Fallback(response, response.Trim());
        }

        return Fallback(response, response.Trim());
    }

    private static InvoiceSummaryResult Fallback(string rawResponse, string summary) =>
        new(
            summary,
            new InvoiceClassification("needs_review", "medium", "The model response was not valid classification JSON."),
            rawResponse);

    private static string Normalize(string? value, string fallback) =>
        string.IsNullOrWhiteSpace(value) ? fallback : value.Trim().ToLowerInvariant();

    private sealed record InferenceResponse(string? Summary, string? Category, string? Risk, string? Rationale);
}
