using IAuto.DocumentProcessing.Abstractions;
using IAuto.DocumentProcessing.Models;
using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.Mvc;
using Microsoft.Azure.Functions.Worker;
using Microsoft.Extensions.Logging;

namespace IAuto.DocumentProcessing.Functions.Functions;

/// <summary>
/// HTTP-triggered entry point for synchronous, on-demand document processing. Accepts a raw
/// document body (for example <c>application/pdf</c> or <c>application/octet-stream</c>) and
/// returns the routing result as JSON. Useful for testing the pipeline and for interactive
/// (attended) reprocessing of a single document.
/// </summary>
public sealed class DocumentHttpTriggerFunction
{
    private readonly IDocumentProcessingPipeline _pipeline;
    private readonly ILogger<DocumentHttpTriggerFunction> _logger;

    /// <summary>Create the HTTP-trigger function.</summary>
    /// <param name="pipeline">The document-processing pipeline.</param>
    /// <param name="logger">Logger for diagnostics.</param>
    public DocumentHttpTriggerFunction(
        IDocumentProcessingPipeline pipeline,
        ILogger<DocumentHttpTriggerFunction> logger)
    {
        ArgumentNullException.ThrowIfNull(pipeline);
        ArgumentNullException.ThrowIfNull(logger);
        _pipeline = pipeline;
        _logger = logger;
    }

    /// <summary>Process a document supplied in the HTTP request body.</summary>
    /// <param name="request">The incoming HTTP request (raw document bytes in the body).</param>
    /// <param name="cancellationToken">Host cancellation token.</param>
    /// <returns>The routing result as JSON, or a 400 when the body is empty.</returns>
    [Function(nameof(DocumentHttpTriggerFunction))]
    public async Task<IActionResult> RunAsync(
        [HttpTrigger(AuthorizationLevel.Function, "post", Route = "documents")] HttpRequest request,
        CancellationToken cancellationToken)
    {
        ArgumentNullException.ThrowIfNull(request);

        string documentName = request.Query["name"].FirstOrDefault() ?? "uploaded-document";
        string? modelId = request.Query["model"].FirstOrDefault();

        using var memory = new MemoryStream();
        await request.Body.CopyToAsync(memory, cancellationToken).ConfigureAwait(false);
        if (memory.Length == 0)
        {
            Log.HttpRejected(_logger, "empty request body");
            return new BadRequestObjectResult("Request body must contain the document bytes.");
        }

        Log.HttpReceived(_logger, documentName, modelId ?? "(default)");
        var analysisRequest = new DocumentAnalysisRequest(
            documentName,
            BinaryData.FromBytes(memory.ToArray()),
            request.ContentType,
            modelId);

        DocumentProcessingResult result = await _pipeline.ProcessAsync(analysisRequest, cancellationToken)
            .ConfigureAwait(false);

        Log.DocumentProcessed(_logger, documentName, result.Status);
        return new OkObjectResult(result);
    }
}
