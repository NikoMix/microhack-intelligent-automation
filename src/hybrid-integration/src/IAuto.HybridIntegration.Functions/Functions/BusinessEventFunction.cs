using System.Net;
using System.Text.Json;
using IAuto.HybridIntegration.Functions.Models;
using IAuto.HybridIntegration.Functions.Services;
using Microsoft.Azure.Functions.Worker;
using Microsoft.Azure.Functions.Worker.Http;
using Microsoft.Extensions.Logging;

namespace IAuto.HybridIntegration.Functions.Functions;

/// <summary>HTTP endpoint fronted by API Management for migrated Power Automate business events.</summary>
public sealed partial class BusinessEventFunction(BusinessEventProcessor processor, ILogger<BusinessEventFunction> logger)
{
    private static readonly JsonSerializerOptions JsonOptions = new(JsonSerializerDefaults.Web);

    /// <summary>Accept, enrich, and route a business event.</summary>
    [Function("ProcessBusinessEvent")]
    public async Task<HttpResponseData> RunAsync(
        [HttpTrigger(AuthorizationLevel.Function, "post", Route = "business-events")] HttpRequestData request,
        CancellationToken cancellationToken)
    {
        ArgumentNullException.ThrowIfNull(request);

        try
        {
            var payload = await JsonSerializer.DeserializeAsync<BusinessEventRequest>(
                request.Body,
                JsonOptions,
                cancellationToken).ConfigureAwait(false);
            if (payload is null)
            {
                return await CreateJsonResponseAsync(request, HttpStatusCode.BadRequest, new { error = "Request body is required." }, cancellationToken)
                    .ConfigureAwait(false);
            }

            var correlationId = GetHeaderValue(request, "x-correlation-id");
            var result = await processor.ProcessAsync(payload, correlationId, cancellationToken).ConfigureAwait(false);
            var response = await CreateJsonResponseAsync(request, HttpStatusCode.OK, result, cancellationToken).ConfigureAwait(false);
            response.Headers.Add("x-correlation-id", result.CorrelationId);
            return response;
        }
        catch (JsonException ex)
        {
            LogInvalidJson(logger, ex);
            return await CreateJsonResponseAsync(request, HttpStatusCode.BadRequest, new { error = "Request body must be valid JSON." }, cancellationToken)
                .ConfigureAwait(false);
        }
        catch (BusinessEventValidationException ex)
        {
            LogValidationFailed(logger, ex);
            return await CreateJsonResponseAsync(request, HttpStatusCode.BadRequest, new { error = ex.Message }, cancellationToken)
                .ConfigureAwait(false);
        }
    }

    [LoggerMessage(EventId = 1001, Level = LogLevel.Warning, Message = "Invalid JSON received by integration bridge.")]
    private static partial void LogInvalidJson(ILogger logger, Exception exception);

    [LoggerMessage(EventId = 1002, Level = LogLevel.Warning, Message = "Business event validation failed.")]
    private static partial void LogValidationFailed(ILogger logger, Exception exception);

    private static string? GetHeaderValue(HttpRequestData request, string name) =>
        request.Headers.TryGetValues(name, out var values) ? values.FirstOrDefault() : null;

    private static async Task<HttpResponseData> CreateJsonResponseAsync<T>(
        HttpRequestData request,
        HttpStatusCode statusCode,
        T body,
        CancellationToken cancellationToken)
    {
        var response = request.CreateResponse(statusCode);
        response.Headers.Add("Content-Type", "application/json; charset=utf-8");
        await JsonSerializer.SerializeAsync(response.Body, body, JsonOptions, cancellationToken).ConfigureAwait(false);
        return response;
    }
}

