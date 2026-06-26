using IAuto.DocumentProcessing.HumanInTheLoop;
using IAuto.DocumentProcessing.Models;
using IAuto.DocumentProcessing.Pipeline;

namespace IAuto.DocumentProcessing.Tests;

/// <summary>Unit tests for the pure auto-approve vs human-review routing logic.</summary>
public sealed class ReviewRoutingTests
{
    private static DocumentExtractionResult Extraction(double? confidence, params ExtractedField[] fields) =>
        new()
        {
            ModelId = "prebuilt-invoice",
            OverallConfidence = confidence,
            Fields = fields,
        };

    private static DocumentProcessingOptions Options(double threshold = 0.80, params string[] required)
    {
        var options = new DocumentProcessingOptions { ConfidenceThreshold = threshold };
        foreach (string field in required)
        {
            options.RequiredFields.Add(field);
        }

        return options;
    }

    [Fact]
    public void Evaluate_AutoApproves_WhenConfidenceClearsThreshold_AndFieldsPresent()
    {
        DocumentExtractionResult extraction = Extraction(0.95, new ExtractedField("InvoiceTotal", "100", 0.95, "Currency"));

        ReviewDecision decision = ReviewRouting.Evaluate(extraction, Options(0.80, "InvoiceTotal"));

        Assert.Equal(DocumentProcessingStatus.AutoApproved, decision.Status);
        Assert.Empty(decision.Reasons);
    }

    [Fact]
    public void Evaluate_RoutesToReview_WhenConfidenceBelowThreshold()
    {
        DocumentExtractionResult extraction = Extraction(0.50, new ExtractedField("InvoiceTotal", "100", 0.50, "Currency"));

        ReviewDecision decision = ReviewRouting.Evaluate(extraction, Options(0.80));

        Assert.Equal(DocumentProcessingStatus.PendingReview, decision.Status);
        Assert.Single(decision.Reasons);
    }

    [Fact]
    public void Evaluate_RoutesToReview_WhenConfidenceMissing()
    {
        ReviewDecision decision = ReviewRouting.Evaluate(Extraction(null), Options(0.80));

        Assert.Equal(DocumentProcessingStatus.PendingReview, decision.Status);
        Assert.Contains(decision.Reasons, r => r.Contains("confidence", StringComparison.OrdinalIgnoreCase));
    }

    [Fact]
    public void Evaluate_RoutesToReview_WhenRequiredFieldMissing()
    {
        DocumentExtractionResult extraction = Extraction(0.99);

        ReviewDecision decision = ReviewRouting.Evaluate(extraction, Options(0.80, "InvoiceTotal"));

        Assert.Equal(DocumentProcessingStatus.PendingReview, decision.Status);
        Assert.Contains(decision.Reasons, r => r.Contains("InvoiceTotal", StringComparison.Ordinal));
    }

    [Fact]
    public void Evaluate_RoutesToReview_WhenRequiredFieldEmpty()
    {
        DocumentExtractionResult extraction = Extraction(0.99, new ExtractedField("InvoiceTotal", "   ", 0.99, "Currency"));

        ReviewDecision decision = ReviewRouting.Evaluate(extraction, Options(0.80, "InvoiceTotal"));

        Assert.Equal(DocumentProcessingStatus.PendingReview, decision.Status);
    }

    [Fact]
    public void Evaluate_Throws_WhenArgumentsNull()
    {
        Assert.Throws<ArgumentNullException>(() => ReviewRouting.Evaluate(null!, Options()));
        Assert.Throws<ArgumentNullException>(() => ReviewRouting.Evaluate(Extraction(0.9), null!));
    }
}
