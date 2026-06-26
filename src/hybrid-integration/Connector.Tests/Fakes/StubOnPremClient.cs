using IAuto.HybridIntegration.Connector.Models;
using IAuto.HybridIntegration.Connector.Services;

namespace IAuto.HybridIntegration.Connector.Tests.Fakes;

/// <summary>In-memory <see cref="IOnPremClient"/> returning a preset order (or none).</summary>
internal sealed class StubOnPremClient : IOnPremClient
{
    public OnPremOrder? Order { get; set; }

    public string? LastOrderId { get; private set; }

    public Task<OnPremOrder?> GetOrderAsync(string orderId, CancellationToken cancellationToken = default)
    {
        LastOrderId = orderId;
        return Task.FromResult(Order);
    }
}
