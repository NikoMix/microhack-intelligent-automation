using IAuto.HybridIntegration.Functions.Models;
using IAuto.HybridIntegration.Functions.Services;
using Xunit;

namespace IAuto.HybridIntegration.Tests;

public sealed class BusinessEventProcessorTests
{
    [Fact]
    public async Task ProcessAsyncHighValueEventReturnsHighPriorityRoutingAsync()
    {
        var processor = new BusinessEventProcessor(new StubInferenceGateway("Approve with finance review."));
        var request = new BusinessEventRequest
        {
            EventId = "order-100",
            EventType = "order.created",
            SourceSystem = "sap",
            CustomerId = "contoso",
            Amount = 12_000m,
            Currency = "EUR",
        };

        var result = await processor.ProcessAsync(request, "corr-1", CancellationToken.None);

        Assert.True(result.Accepted);
        Assert.Equal("order-100", result.EventId);
        Assert.Equal("corr-1", result.CorrelationId);
        Assert.Equal("High", result.Routing.Priority);
        Assert.Equal("approvals-high-value", result.Routing.Target);
        Assert.Equal("Approve with finance review.", result.Enrichment.Summary);
    }

    [Fact]
    public async Task ProcessAsyncStandardOrderReturnsStraightThroughRoutingAsync()
    {
        var processor = new BusinessEventProcessor(new StubInferenceGateway("Standard fulfillment."));
        var request = new BusinessEventRequest
        {
            EventType = "order.created",
            SourceSystem = "dynamics",
            Amount = 120m,
            Currency = "USD",
        };

        var result = await processor.ProcessAsync(request, null, CancellationToken.None);

        Assert.StartsWith("evt-", result.EventId, StringComparison.Ordinal);
        Assert.Equal(result.EventId, result.CorrelationId);
        Assert.Equal("Standard", result.Routing.Priority);
        Assert.Equal("orders-standard", result.Routing.Target);
    }

    [Theory]
    [InlineData("", "source", 10, "eventType is required.")]
    [InlineData("order.created", "", 10, "sourceSystem is required.")]
    [InlineData("order.created", "source", -1, "amount must be zero or greater.")]
    public async Task ProcessAsyncInvalidRequestThrowsValidationExceptionAsync(
        string eventType,
        string sourceSystem,
        decimal amount,
        string expectedMessage)
    {
        var processor = new BusinessEventProcessor(new StubInferenceGateway("unused"));
        var request = new BusinessEventRequest
        {
            EventType = eventType,
            SourceSystem = sourceSystem,
            Amount = amount,
        };

        var ex = await Assert.ThrowsAsync<BusinessEventValidationException>(
            () => processor.ProcessAsync(request, null, CancellationToken.None));

        Assert.Equal(expectedMessage, ex.Message);
    }

    private sealed class StubInferenceGateway(string summary) : IInferenceGateway
    {
        public Task<EventEnrichment> EnrichAsync(BusinessEventRequest request, CancellationToken cancellationToken) =>
            Task.FromResult(new EventEnrichment
            {
                Summary = summary,
                Model = "stub-model",
            });
    }
}


