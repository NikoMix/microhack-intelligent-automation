using System.Net;
using System.Net.Http.Json;
using IAuto.HybridIntegration.OnPremStub;
using IAuto.HybridIntegration.OnPremStub.Models;
using Microsoft.AspNetCore.Mvc.Testing;

namespace IAuto.HybridIntegration.Connector.Tests;

/// <summary>
/// Integration tests that boot the on-prem stub in memory via <see cref="WebApplicationFactory{T}"/>
/// and exercise its HTTP surface end to end.
/// </summary>
public sealed class OnPremStubEndpointsTests : IClassFixture<WebApplicationFactory<OnPremStubApi>>
{
    private readonly WebApplicationFactory<OnPremStubApi> _factory;

    public OnPremStubEndpointsTests(WebApplicationFactory<OnPremStubApi> factory) => _factory = factory;

    [Fact]
    public async Task Health_Returns200()
    {
        using var client = _factory.CreateClient();

        using var response = await client.GetAsync(new Uri("/health", UriKind.Relative));

        response.EnsureSuccessStatusCode();
        var payload = await response.Content.ReadFromJsonAsync<HealthDto>();
        Assert.Equal("healthy", payload!.Status);
    }

    [Fact]
    public async Task GetOrders_ReturnsSeededOrders()
    {
        using var client = _factory.CreateClient();

        var orders = await client.GetFromJsonAsync<IReadOnlyList<OrderStatus>>(
            new Uri("/orders", UriKind.Relative));

        Assert.NotNull(orders);
        Assert.Equal(3, orders!.Count);
    }

    [Fact]
    public async Task GetOrder_KnownId_Returns200()
    {
        using var client = _factory.CreateClient();

        var order = await client.GetFromJsonAsync<OrderStatus>(
            new Uri("/orders/ORD-1001", UriKind.Relative));

        Assert.NotNull(order);
        Assert.Equal("ORD-1001", order!.OrderId);
        Assert.Equal("Shipped", order.Status);
    }

    [Fact]
    public async Task GetOrder_UnknownId_Returns404()
    {
        using var client = _factory.CreateClient();

        using var response = await client.GetAsync(new Uri("/orders/ORD-0000", UriKind.Relative));

        Assert.Equal(HttpStatusCode.NotFound, response.StatusCode);
    }

    private sealed record HealthDto(string Status);
}
