using Azure;
using Azure.AI.DocumentIntelligence;
using IAuto.DocumentProcessing.Abstractions;
using IAuto.DocumentProcessing.Models;
using IAuto.DocumentProcessing.Pipeline;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Options;

namespace IAuto.DocumentProcessing.DocumentIntelligence;

/// <summary>
/// <see cref="IDocumentAnalyzer"/> backed by Azure AI Document Intelligence. Uses the
/// configured default model when a request does not specify one.
/// </summary>
public sealed class DocumentIntelligenceAnalyzer : IDocumentAnalyzer
{
    private readonly DocumentIntelligenceClient _client;
    private readonly string _defaultModelId;
    private readonly ILogger<DocumentIntelligenceAnalyzer> _logger;

    /// <summary>Create an analyzer from an SDK client and pipeline options.</summary>
    /// <param name="client">The Document Intelligence client.</param>
    /// <param name="options">Pipeline options supplying the default model id.</param>
    /// <param name="logger">Logger for diagnostics.</param>
    public DocumentIntelligenceAnalyzer(
        DocumentIntelligenceClient client,
        IOptions<DocumentProcessingOptions> options,
        ILogger<DocumentIntelligenceAnalyzer> logger)
    {
        ArgumentNullException.ThrowIfNull(client);
        ArgumentNullException.ThrowIfNull(options);
        ArgumentNullException.ThrowIfNull(logger);
        _client = client;
        _defaultModelId = options.Value.DefaultModelId;
        _logger = logger;
    }

    /// <inheritdoc />
    public async Task<DocumentExtractionResult> AnalyzeAsync(
        DocumentAnalysisRequest request,
        CancellationToken cancellationToken = default)
    {
        ArgumentNullException.ThrowIfNull(request);
        string modelId = string.IsNullOrWhiteSpace(request.ModelId) ? _defaultModelId : request.ModelId;

        Log.AnalyzingDocument(_logger, request.DocumentName, modelId);

        Operation<AnalyzeResult> operation = await _client.AnalyzeDocumentAsync(
            WaitUntil.Completed,
            modelId,
            request.Content,
            cancellationToken: cancellationToken).ConfigureAwait(false);

        DocumentExtractionResult result = DocumentResultMapper.Map(modelId, operation.Value);
        Log.AnalyzedDocument(
            _logger,
            request.DocumentName,
            result.Fields.Count,
            result.OverallConfidence ?? double.NaN);
        return result;
    }
}
