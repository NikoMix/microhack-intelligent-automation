using IAuto.HybridIntegration.OnPremStub;
using IAuto.HybridIntegration.OnPremStub.Models;

namespace IAuto.HybridIntegration.Connector.Tests;

/// <summary>Unit tests for the on-prem stub's <see cref="OrderRepository"/>.</summary>
public sealed class OrderRepositoryTests
{
    [Fact]
    public void GetAll_ReturnsSeededOrders()
    {
        var repository = new OrderRepository();

        var orders = repository.GetAll();

        Assert.Equal(3, orders.Count);
        Assert.Contains(orders, o => o.OrderId == "ORD-1001");
        Assert.Contains(orders, o => o.OrderId == "ORD-1002");
        Assert.Contains(orders, o => o.OrderId == "ORD-1003");
    }

    [Theory]
    [InlineData("ORD-1001")]
    [InlineData("ord-1001")]
    [InlineData("Ord-1001")]
    public void TryGet_KnownId_IsCaseInsensitive(string id)
    {
        var repository = new OrderRepository();

        var found = repository.TryGet(id, out var order);

        Assert.True(found);
        Assert.NotNull(order);
        Assert.Equal("ORD-1001", order!.OrderId);
    }

    [Fact]
    public void TryGet_UnknownId_ReturnsFalse()
    {
        var repository = new OrderRepository();

        var found = repository.TryGet("ORD-0000", out var order);

        Assert.False(found);
        Assert.Null(order);
    }

    [Theory]
    [InlineData("")]
    [InlineData("   ")]
    public void TryGet_BlankId_ReturnsFalse(string id)
    {
        var repository = new OrderRepository();

        var found = repository.TryGet(id, out var order);

        Assert.False(found);
        Assert.Null(order);
    }

    [Fact]
    public void Ctor_WithExplicitSeed_ExposesProvidedOrders()
    {
        var seed = new[]
        {
            new OrderStatus("X-1", "Cust", "Processing", null, null, null, DateTimeOffset.UnixEpoch),
        };
        var repository = new OrderRepository(seed);

        Assert.Single(repository.GetAll());
        Assert.True(repository.TryGet("x-1", out _));
    }
}
