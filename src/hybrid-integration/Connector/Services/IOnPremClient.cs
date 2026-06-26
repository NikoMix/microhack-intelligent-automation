using IAuto.HybridIntegration.Connector.Models;

namespace IAuto.HybridIntegration.Connector.Services;

/// <summary>
/// Abstraction over the on-prem line-of-business system. Keeping this behind an interface
/// lets the enricher be unit-tested without any HTTP or hybrid-connectivity dependency.
/// </summary>
public interface IOnPremClient
{
    /// <summary>Resolve a single order from the on-prem system.</summary>
    /// <param name="orderId">Business id of the order.</param>
    /// <param name="cancellationToken">Token used to cancel the call.</param>
    /// <returns>The order, or <see langword="null"/> when it does not exist.</returns>
    Task<OnPremOrder?> GetOrderAsync(string orderId, CancellationToken cancellationToken = default);
}
