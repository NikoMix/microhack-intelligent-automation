using IAuto.DocumentProcessing.Inference;
using IAuto.DocumentProcessing.Models;
using IAuto.DocumentProcessing.Tests.Fakes;
using Xunit;

namespace IAuto.DocumentProcessing.Tests;

public sealed class InferenceInvoiceSummarizerTests
{
    [Fact]
    public async Task SummarizeAsync_ParsesStrictJsonClassificationAsync()
    {
        var inference = new StubInvoiceSummaryInference("""
            { "summary": "Contoso submitted invoice INV-1007 for USD 1,245.50.", "category": "standard", "risk": "low", "rationale": "Complete invoice fields and normal value." }
            """);
        var summarizer = new InferenceInvoiceSummarizer(inference);
        var invoice = new InvoiceAnalysis(
            "Contoso Office Supplies",
            "INV-1007",
            new DateOnly(2026, 6, 1),
            "USD",
            1245.50m,
            [new InvoiceLineItem("Docking stations", 4, 199.50m, 798.00m)],
            0.96);

        var result = await summarizer.SummarizeAsync(invoice, CancellationToken.None);

        Assert.Equal("Contoso submitted invoice INV-1007 for USD 1,245.50.", result.Summary);
        Assert.Equal("standard", result.Classification.Category);
        Assert.Equal("low", result.Classification.Risk);
        Assert.Contains("normal value", result.Classification.Rationale, StringComparison.OrdinalIgnoreCase);
        Assert.Contains("prebuilt", inference.LastUserPrompt ?? string.Empty, StringComparison.OrdinalIgnoreCase);
    }

    [Fact]
    public async Task SummarizeAsync_FallsBackWhenModelReturnsPlainTextAsync()
    {
        var summarizer = new InferenceInvoiceSummarizer(new StubInvoiceSummaryInference("Invoice needs manual review."));
        var invoice = new InvoiceAnalysis(null, null, null, null, null, [], null);

        var result = await summarizer.SummarizeAsync(invoice, CancellationToken.None);

        Assert.Equal("Invoice needs manual review.", result.Summary);
        Assert.Equal("needs_review", result.Classification.Category);
        Assert.Equal("medium", result.Classification.Risk);
    }
}


