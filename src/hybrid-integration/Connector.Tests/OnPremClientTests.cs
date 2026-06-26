using System.Net;
using System.Net.Http.Json;
using IAuto.HybridIntegration.Connector.Services;
using IAuto.HybridIntegration.Connector.Tests.Fakes;
using Microsoft.Extensions.Logging.Abstractions;

namespace IAuto.HybridIntegration.Connector.Tests;

/// <summary>Unit tests for the typed <see cref="OnPremClient"/>.</summary>
public sealed class OnPremClientTests
{
    private static readonly Uri BaseAddress = new("https://onprem.test/");

    private static OnPremClient CreateClient(StubHttpMessageHandler handler) =>
        new(new HttpClient(handler) { BaseAddress = BaseAddress }, NullLogger<OnPremClient>.Instance);

    [Fact]
    public async Task GetOrderAsync_WhenFound_DeserializesOrder()
    {
        var handler = new StubHttpMessageHandler(_ => new HttpResponseMessage(HttpStatusCode.OK)
        {
            Content = JsonContent.Create(new
            {
                orderId = "ORD-1001",
                customer = "Contoso Retail",
                status = "Shipped",
                carrier = "Northwind Freight",
                trackingNumber = "NF-88421156",
                estimatedDelivery = "2026-07-02",
                lastUpdatedUtc = "2026-06-26T08:30:00+00:00",
            }),
        });
        var client = CreateClient(handler);

        var order = await client.GetOrderAsync("ORD-1001");

        Assert.NotNull(order);
        Assert.Equal("ORD-1001", order!.OrderId);
        Assert.Equal("Contoso Retail", order.Customer);
        Assert.Equal("Shipped", order.Status);
        Assert.Equal("Northwind Freight", order.Carrier);
        Assert.Equal(new DateOnly(2026, 7, 2), order.EstimatedDelivery);
    }

    [Fact]
    public async Task GetOrderAsync_WhenNotFound_ReturnsNull()
    {
        var handler = new StubHttpMessageHandler(_ => new HttpResponseMessage(HttpStatusCode.NotFound));
        var client = CreateClient(handler);

        var order = await client.GetOrderAsync("ORD-404");

        Assert.Null(order);
    }

    [Fact]
    public async Task GetOrderAsync_EscapesOrderIdInPath()
    {
        var handler = new StubHttpMessageHandler(_ => new HttpResponseMessage(HttpStatusCode.NotFound));
        var client = CreateClient(handler);

        await client.GetOrderAsync("ORD/1001");

        Assert.NotNull(handler.LastRequest);
        Assert.Contains("orders/ORD%2F1001", handler.LastRequest!.RequestUri!.AbsoluteUri, StringComparison.Ordinal);
    }

    [Fact]
    public async Task GetOrderAsync_WhenServerErrors_Throws()
    {
        var handler = new StubHttpMessageHandler(_ => new HttpResponseMessage(HttpStatusCode.InternalServerError));
        var client = CreateClient(handler);

        await Assert.ThrowsAsync<HttpRequestException>(() => client.GetOrderAsync("ORD-1001"));
    }

    [Fact]
    public async Task GetOrderAsync_BlankId_Throws()
    {
        var handler = new StubHttpMessageHandler(_ => new HttpResponseMessage(HttpStatusCode.OK));
        var client = CreateClient(handler);

        await Assert.ThrowsAsync<ArgumentException>(() => client.GetOrderAsync("  "));
    }
}
