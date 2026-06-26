using IAuto.DocumentProcessing.Abstractions;
using IAuto.DocumentProcessing.Models;
using Microsoft.Azure.Functions.Worker;
using Microsoft.Extensions.Logging;

namespace IAuto.DocumentProcessing.Functions.Functions;

/// <summary>
/// Blob-triggered entry point. When a document lands in the input container, run it through
/// the processing pipeline. Uses an Event Grid source, which the Flex Consumption plan requires
/// (replacing the legacy container-polling trigger).
/// </summary>
public sealed class DocumentBlobTriggerFunction
{
    private const string InputContainer = "incoming-documents";

    private readonly IDocumentProcessingPipeline _pipeline;
    private readonly ILogger<DocumentBlobTriggerFunction> _logger;

    /// <summary>Create the blob-trigger function.</summary>
    /// <param name="pipeline">The document-processing pipeline.</param>
    /// <param name="logger">Logger for diagnostics.</param>
    public DocumentBlobTriggerFunction(
        IDocumentProcessingPipeline pipeline,
        ILogger<DocumentBlobTriggerFunction> logger)
    {
        ArgumentNullException.ThrowIfNull(pipeline);
        ArgumentNullException.ThrowIfNull(logger);
        _pipeline = pipeline;
        _logger = logger;
    }

    /// <summary>Process a newly uploaded document blob.</summary>
    /// <param name="content">Raw blob content.</param>
    /// <param name="name">Blob name bound from the trigger path.</param>
    /// <param name="cancellationToken">Host cancellation token.</param>
    /// <returns>A task that completes when processing finishes.</returns>
    [Function(nameof(DocumentBlobTriggerFunction))]
    public async Task RunAsync(
        [BlobTrigger(InputContainer + "/{name}", Source = BlobTriggerSource.EventGrid)] byte[] content,
        string name,
        CancellationToken cancellationToken)
    {
        ArgumentNullException.ThrowIfNull(content);
        Log.BlobReceived(_logger, name, content.Length);

        var request = new DocumentAnalysisRequest(name, BinaryData.FromBytes(content));
        DocumentProcessingResult result = await _pipeline.ProcessAsync(request, cancellationToken)
            .ConfigureAwait(false);

        Log.DocumentProcessed(_logger, name, result.Status);
    }
}
