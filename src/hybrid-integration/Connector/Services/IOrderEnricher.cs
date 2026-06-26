using IAuto.HybridIntegration.Connector.Models;

namespace IAuto.HybridIntegration.Connector.Services;

/// <summary>
/// Orchestrates the hybrid flow: fetch an order from on-prem, then answer the customer's
/// question with the modular-inference model. Depends only on abstractions so it can run
/// against any inference provider and any on-prem implementation.
/// </summary>
public interface IOrderEnricher
{
    /// <summary>Resolve the order and produce a grounded, natural-language answer.</summary>
    /// <param name="request">The order id and customer question.</param>
    /// <param name="cancellationToken">Token used to cancel the operation.</param>
    /// <returns>The enrichment result, including the provider/model used.</returns>
    Task<EnrichmentResult> EnrichAsync(
        EnrichmentRequest request,
        CancellationToken cancellationToken = default);
}
