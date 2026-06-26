using IAuto.HybridIntegration.Connector.Models;
using IAuto.HybridIntegration.Connector.Services;

namespace IAuto.HybridIntegration.Connector.Tests.Fakes;

/// <summary>In-memory <see cref="IOrderEnricher"/> returning a preset result for function tests.</summary>
internal sealed class StubOrderEnricher : IOrderEnricher
{
    public EnrichmentRequest? LastRequest { get; private set; }

    public EnrichmentResult Result { get; set; } = new()
    {
        OrderId = "ORD-1001",
        Found = true,
        Status = "Shipped",
        Answer = "Your order has shipped.",
        Provider = "github",
        Model = "openai/gpt-4o-mini",
    };

    public Task<EnrichmentResult> EnrichAsync(
        EnrichmentRequest request,
        CancellationToken cancellationToken = default)
    {
        LastRequest = request;
        return Task.FromResult(Result);
    }
}
