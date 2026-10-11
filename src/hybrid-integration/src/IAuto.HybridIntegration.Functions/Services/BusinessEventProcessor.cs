using System.Diagnostics;
using IAuto.HybridIntegration.Functions.Models;

namespace IAuto.HybridIntegration.Functions.Services;

/// <summary>Coordinates validation, inference enrichment, and deterministic routing for migrated business events.</summary>
public sealed class BusinessEventProcessor(IInferenceGateway inferenceGateway)
{
    /// <summary>ActivitySource name used by OpenTelemetry tracing.</summary>
    public const string ActivitySourceName = "IAuto.HybridIntegration.BusinessEventProcessor";

    private const decimal HighValueThreshold = 5_000m;
    private static readonly ActivitySource ActivitySource = new(ActivitySourceName);

    /// <summary>Process a legacy automation event and return the structured bridge result.</summary>
    public async Task<BusinessEventResponse> ProcessAsync(
        BusinessEventRequest request,
        string? correlationId,
        CancellationToken cancellationToken)
    {
        ArgumentNullException.ThrowIfNull(request);
        Validate(request);

        using var activity = ActivitySource.StartActivity("ProcessBusinessEvent", ActivityKind.Internal);
        var resolvedEventId = string.IsNullOrWhiteSpace(request.EventId)
            ? $"evt-{Guid.NewGuid():N}"
            : request.EventId.Trim();
        var resolvedCorrelationId = string.IsNullOrWhiteSpace(correlationId)
            ? resolvedEventId
            : correlationId.Trim();

        activity?.SetTag("event.id", resolvedEventId);
        activity?.SetTag("event.type", request.EventType);
        activity?.SetTag("source.system", request.SourceSystem);

        var enrichment = await inferenceGateway.EnrichAsync(request, cancellationToken).ConfigureAwait(false);
        var routing = BuildRoutingDecision(request);

        return new BusinessEventResponse
        {
            EventId = resolvedEventId,
            CorrelationId = resolvedCorrelationId,
            Accepted = true,
            Enrichment = enrichment,
            Routing = routing,
        };
    }

    private static void Validate(BusinessEventRequest request)
    {
        if (string.IsNullOrWhiteSpace(request.EventType))
        {
            throw new BusinessEventValidationException("eventType is required.");
        }

        if (string.IsNullOrWhiteSpace(request.SourceSystem))
        {
            throw new BusinessEventValidationException("sourceSystem is required.");
        }

        if (request.Amount < 0)
        {
            throw new BusinessEventValidationException("amount must be zero or greater.");
        }
    }

    private static RoutingDecision BuildRoutingDecision(BusinessEventRequest request)
    {
        if (request.Amount >= HighValueThreshold || request.EventType.Contains("approval", StringComparison.OrdinalIgnoreCase))
        {
            return new RoutingDecision
            {
                Priority = "High",
                Target = "approvals-high-value",
                Reason = "High-value or approval-related events require explicit review.",
            };
        }

        return new RoutingDecision
        {
            Priority = "Standard",
            Target = "orders-standard",
            Reason = "Event is eligible for straight-through processing.",
        };
    }
}

/// <summary>Validation failure returned as HTTP 400 by the Functions endpoint.</summary>
public sealed class BusinessEventValidationException(string message) : Exception(message)
{
}
