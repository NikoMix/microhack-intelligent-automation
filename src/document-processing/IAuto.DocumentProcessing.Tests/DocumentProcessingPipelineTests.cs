using IAuto.DocumentProcessing.Abstractions;
using IAuto.DocumentProcessing.Models;
using IAuto.DocumentProcessing.Pipeline;
using IAuto.DocumentProcessing.Tests.Fakes;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.Extensions.Options;

namespace IAuto.DocumentProcessing.Tests;

/// <summary>End-to-end pipeline behaviour using fakes for the analyzer, insights, and approval queue.</summary>
public sealed class DocumentProcessingPipelineTests
{
    private static DocumentAnalysisRequest Request() =>
        new("invoice.pdf", BinaryData.FromString("bytes"));

    private static DocumentExtractionResult Extraction(double confidence) =>
        new()
        {
            ModelId = "prebuilt-invoice",
            OverallConfidence = confidence,
            Content = "content",
            Fields = [new ExtractedField("InvoiceTotal", "100", confidence, "Currency")],
        };

    private static DocumentProcessingPipeline Create(
        IDocumentAnalyzer analyzer,
        IApprovalQueueWriter writer,
        IDocumentInsightGenerator insights,
        DocumentProcessingOptions options) =>
        new(analyzer, insights, writer, Options.Create(options), NullLogger<DocumentProcessingPipeline>.Instance);

    [Fact]
    public async Task ProcessAsync_AutoApproves_WhenConfident()
    {
        var analyzer = new FakeDocumentAnalyzer { Result = Extraction(0.95) };
        var writer = new RecordingApprovalWriter();
        DocumentProcessingPipeline pipeline = Create(
            analyzer, writer, new FakeInsightGenerator(), new DocumentProcessingOptions { ConfidenceThreshold = 0.80 });

        DocumentProcessingResult result = await pipeline.ProcessAsync(Request());

        Assert.Equal(DocumentProcessingStatus.AutoApproved, result.Status);
        Assert.Equal(0, writer.CallCount);
        Assert.Null(result.ApprovalReference);
        Assert.NotNull(result.Extraction);
    }

    [Fact]
    public async Task ProcessAsync_RoutesToReview_WhenLowConfidence()
    {
        var analyzer = new FakeDocumentAnalyzer { Result = Extraction(0.40) };
        var writer = new RecordingApprovalWriter { ReturnId = "ref-9" };
        DocumentProcessingPipeline pipeline = Create(
            analyzer, writer, new FakeInsightGenerator(), new DocumentProcessingOptions { ConfidenceThreshold = 0.80 });

        DocumentProcessingResult result = await pipeline.ProcessAsync(Request());

        Assert.Equal(DocumentProcessingStatus.PendingReview, result.Status);
        Assert.Equal(1, writer.CallCount);
        Assert.Equal("ref-9", result.ApprovalReference);
        Assert.NotNull(writer.LastRequest);
        Assert.NotEmpty(writer.LastRequest!.Reasons);
        Assert.Single(writer.LastRequest.Fields);
    }

    [Fact]
    public async Task ProcessAsync_ReturnsFailed_WhenAnalyzerThrows()
    {
        var analyzer = new FakeDocumentAnalyzer { Exception = new InvalidOperationException("boom") };
        var writer = new RecordingApprovalWriter();
        DocumentProcessingPipeline pipeline = Create(
            analyzer, writer, new FakeInsightGenerator(), new DocumentProcessingOptions());

        DocumentProcessingResult result = await pipeline.ProcessAsync(Request());

        Assert.Equal(DocumentProcessingStatus.Failed, result.Status);
        Assert.Contains("boom", string.Join(" ", result.Reasons), StringComparison.Ordinal);
        Assert.Equal(0, writer.CallCount);
    }

    [Fact]
    public async Task ProcessAsync_AddsInsights_WhenEnabled()
    {
        var analyzer = new FakeDocumentAnalyzer { Result = Extraction(0.95) };
        var insights = new FakeInsightGenerator { Insights = new DocumentInsights("S", "Invoice", null) };
        DocumentProcessingPipeline pipeline = Create(
            analyzer,
            new RecordingApprovalWriter(),
            insights,
            new DocumentProcessingOptions { ConfidenceThreshold = 0.80, EnableInsights = true });

        DocumentProcessingResult result = await pipeline.ProcessAsync(Request());

        Assert.Equal(1, insights.CallCount);
        Assert.NotNull(result.Insights);
        Assert.Equal("Invoice", result.Insights!.Category);
    }

    [Fact]
    public async Task ProcessAsync_SkipsInsights_WhenDisabled()
    {
        var analyzer = new FakeDocumentAnalyzer { Result = Extraction(0.95) };
        var insights = new FakeInsightGenerator { Insights = new DocumentInsights("S", "Invoice", null) };
        DocumentProcessingPipeline pipeline = Create(
            analyzer,
            new RecordingApprovalWriter(),
            insights,
            new DocumentProcessingOptions { ConfidenceThreshold = 0.80, EnableInsights = false });

        DocumentProcessingResult result = await pipeline.ProcessAsync(Request());

        Assert.Equal(0, insights.CallCount);
        Assert.Null(result.Insights);
    }
}
