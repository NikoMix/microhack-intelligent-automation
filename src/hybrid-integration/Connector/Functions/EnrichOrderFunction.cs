using System.Text.Json;
using IAuto.HybridIntegration.Connector.Models;
using IAuto.HybridIntegration.Connector.Services;
using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.Mvc;
using Microsoft.Azure.Functions.Worker;
using Microsoft.Extensions.Logging;

namespace IAuto.HybridIntegration.Connector.Functions;

/// <summary>
/// HTTP-triggered connector invoked by the Logic Apps Standard workflow. It validates the
/// request, delegates to <see cref="IOrderEnricher"/> (on-prem lookup + modular inference), and
/// returns the enrichment result as JSON.
/// </summary>
public sealed partial class EnrichOrderFunction
{
    private readonly IOrderEnricher _enricher;
    private readonly ILogger<EnrichOrderFunction> _logger;

    /// <summary>Create the function from its injected collaborators.</summary>
    /// <param name="enricher">Service that performs the on-prem lookup and inference.</param>
    /// <param name="logger">Logger used for invocation telemetry.</param>
    public EnrichOrderFunction(IOrderEnricher enricher, ILogger<EnrichOrderFunction> logger)
    {
        _enricher = enricher ?? throw new ArgumentNullException(nameof(enricher));
        _logger = logger ?? throw new ArgumentNullException(nameof(logger));
    }

    /// <summary>
    /// Handle <c>POST /api/enrich-order</c>. The body must contain <c>orderId</c> and
    /// <c>question</c>. Returns <c>200</c> with the enrichment result, or <c>400</c> when the
    /// payload is missing or malformed.
    /// </summary>
    /// <param name="request">The incoming HTTP request.</param>
    /// <param name="cancellationToken">Token used to cancel the operation.</param>
    /// <returns>An <see cref="IActionResult"/> describing the outcome.</returns>
    [Function("EnrichOrder")]
    public async Task<IActionResult> RunAsync(
        [HttpTrigger(AuthorizationLevel.Function, "post", Route = "enrich-order")] HttpRequest request,
        CancellationToken cancellationToken)
    {
        ArgumentNullException.ThrowIfNull(request);

        EnrichmentRequest? payload;
        try
        {
            payload = await request
                .ReadFromJsonAsync<EnrichmentRequest>(cancellationToken)
                .ConfigureAwait(false);
        }
        catch (JsonException ex)
        {
            LogMalformedJson(ex);
            return new BadRequestObjectResult(new ErrorResponse("Request body must be valid JSON."));
        }

        if (payload is null ||
            string.IsNullOrWhiteSpace(payload.OrderId) ||
            string.IsNullOrWhiteSpace(payload.Question))
        {
            return new BadRequestObjectResult(
                new ErrorResponse("Both 'orderId' and 'question' are required."));
        }

        LogEnriching(payload.OrderId);
        var result = await _enricher.EnrichAsync(payload, cancellationToken).ConfigureAwait(false);
        return new OkObjectResult(result);
    }

    [LoggerMessage(Level = LogLevel.Warning, Message = "Connector received a malformed JSON body.")]
    private partial void LogMalformedJson(Exception exception);

    [LoggerMessage(Level = LogLevel.Information, Message = "Enriching order {OrderId}.")]
    private partial void LogEnriching(string orderId);
}

/// <summary>Error payload returned for bad requests.</summary>
/// <param name="Error">Human-readable description of the validation failure.</param>
internal sealed record ErrorResponse(string Error);
