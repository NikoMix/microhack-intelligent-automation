using IAuto.HybridIntegration.Functions.Models;

namespace IAuto.HybridIntegration.Functions.Services;

/// <summary>Narrow boundary around the shared modular inference client so handler logic remains testable.</summary>
public interface IInferenceGateway
{
    /// <summary>Generate a concise enrichment for a business event.</summary>
    Task<EventEnrichment> EnrichAsync(BusinessEventRequest request, CancellationToken cancellationToken);
}
