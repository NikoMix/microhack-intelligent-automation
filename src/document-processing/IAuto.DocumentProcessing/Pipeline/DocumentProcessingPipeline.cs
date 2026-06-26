using System.Diagnostics;
using IAuto.DocumentProcessing.Abstractions;
using IAuto.DocumentProcessing.HumanInTheLoop;
using IAuto.DocumentProcessing.Models;
using IAuto.DocumentProcessing.Telemetry;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Options;

namespace IAuto.DocumentProcessing.Pipeline;

/// <summary>
/// Default <see cref="IDocumentProcessingPipeline"/>: analyze → optional insights →
/// confidence and required-field routing → auto-approve or enqueue for human review.
/// </summary>
public sealed class DocumentProcessingPipeline : IDocumentProcessingPipeline
{
    private readonly IDocumentAnalyzer _analyzer;
    private readonly IDocumentInsightGenerator _insightGenerator;
    private readonly IApprovalQueueWriter _approvalWriter;
    private readonly DocumentProcessingOptions _options;
    private readonly ILogger<DocumentProcessingPipeline> _logger;

    /// <summary>Create the pipeline from its collaborators.</summary>
    /// <param name="analyzer">Document Intelligence analyzer.</param>
    /// <param name="insightGenerator">Insight generator (real or no-op).</param>
    /// <param name="approvalWriter">Human-in-the-loop approval queue writer.</param>
    /// <param name="options">Pipeline routing options.</param>
    /// <param name="logger">Logger for diagnostics.</param>
    public DocumentProcessingPipeline(
        IDocumentAnalyzer analyzer,
        IDocumentInsightGenerator insightGenerator,
        IApprovalQueueWriter approvalWriter,
        IOptions<DocumentProcessingOptions> options,
        ILogger<DocumentProcessingPipeline> logger)
    {
        ArgumentNullException.ThrowIfNull(analyzer);
        ArgumentNullException.ThrowIfNull(insightGenerator);
        ArgumentNullException.ThrowIfNull(approvalWriter);
        ArgumentNullException.ThrowIfNull(options);
        ArgumentNullException.ThrowIfNull(logger);
        _analyzer = analyzer;
        _insightGenerator = insightGenerator;
        _approvalWriter = approvalWriter;
        _options = options.Value;
        _logger = logger;
    }

    /// <inheritdoc />
    public async Task<DocumentProcessingResult> ProcessAsync(
        DocumentAnalysisRequest request,
        CancellationToken cancellationToken = default)
    {
        ArgumentNullException.ThrowIfNull(request);
        using Activity? activity = DocumentProcessingDiagnostics.ActivitySource.StartActivity("ProcessDocument");
        activity?.SetTag("document.name", request.DocumentName);

        DocumentExtractionResult extraction;
        try
        {
            extraction = await _analyzer.AnalyzeAsync(request, cancellationToken).ConfigureAwait(false);
        }
        catch (OperationCanceledException)
        {
            throw;
        }
        catch (Exception ex)
        {
            Log.ProcessingFailed(_logger, request.DocumentName, ex);
            DocumentProcessingDiagnostics.RecordFailed();
            activity?.SetStatus(ActivityStatusCode.Error);
            return DocumentProcessingResult.Failed(request.DocumentName, ex.Message);
        }

        DocumentInsights? insights = null;
        if (_options.EnableInsights)
        {
            insights = await _insightGenerator.GenerateAsync(extraction, cancellationToken).ConfigureAwait(false);
        }

        ReviewDecision decision = ReviewRouting.Evaluate(extraction, _options);
        activity?.SetTag("document.status", decision.Status.ToString());

        if (decision.Status == DocumentProcessingStatus.AutoApproved)
        {
            Log.AutoApproved(_logger, request.DocumentName);
            DocumentProcessingDiagnostics.RecordAutoApproved();
            return new DocumentProcessingResult
            {
                DocumentName = request.DocumentName,
                Status = DocumentProcessingStatus.AutoApproved,
                Extraction = extraction,
                Insights = insights,
                Reasons = decision.Reasons,
            };
        }

        var approval = new ApprovalRequest
        {
            DocumentName = request.DocumentName,
            ModelId = extraction.ModelId,
            OverallConfidence = extraction.OverallConfidence,
            Reasons = decision.Reasons,
            Fields = extraction.Fields,
            Insights = insights,
        };
        string reference = await _approvalWriter.EnqueueAsync(approval, cancellationToken).ConfigureAwait(false);

        Log.PendingReview(_logger, request.DocumentName, reference);
        DocumentProcessingDiagnostics.RecordPendingReview();
        return new DocumentProcessingResult
        {
            DocumentName = request.DocumentName,
            Status = DocumentProcessingStatus.PendingReview,
            Extraction = extraction,
            Insights = insights,
            Reasons = decision.Reasons,
            ApprovalReference = reference,
        };
    }
}
