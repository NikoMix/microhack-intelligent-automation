using IAuto.HybridIntegration.OnPremStub.Models;

namespace IAuto.HybridIntegration.OnPremStub;

/// <summary>
/// In-memory, deterministic store of orders standing in for an on-prem database. It is
/// intentionally tiny and seedable so the hybrid sample runs with zero external dependencies
/// and so its behaviour is fully unit-testable without a web host.
/// </summary>
public sealed class OrderRepository
{
    private readonly IReadOnlyDictionary<string, OrderStatus> _orders;

    /// <summary>Create a repository seeded with the built-in demo orders.</summary>
    public OrderRepository()
        : this(SeedData())
    {
    }

    /// <summary>Create a repository from an explicit set of orders (used by tests).</summary>
    /// <param name="orders">Orders to expose. Order ids are matched case-insensitively.</param>
    public OrderRepository(IEnumerable<OrderStatus> orders)
    {
        ArgumentNullException.ThrowIfNull(orders);
        _orders = orders.ToDictionary(o => o.OrderId, StringComparer.OrdinalIgnoreCase);
    }

    /// <summary>Return every known order, ordered by id for stable output.</summary>
    public IReadOnlyCollection<OrderStatus> GetAll() =>
        _orders.Values.OrderBy(o => o.OrderId, StringComparer.OrdinalIgnoreCase).ToArray();

    /// <summary>Look up a single order by its business id.</summary>
    /// <param name="orderId">The order identifier to resolve.</param>
    /// <param name="order">The resolved order when found; otherwise <see langword="null"/>.</param>
    /// <returns><see langword="true"/> when an order was found; otherwise <see langword="false"/>.</returns>
    public bool TryGet(string orderId, out OrderStatus? order)
    {
        if (string.IsNullOrWhiteSpace(orderId))
        {
            order = null;
            return false;
        }

        return _orders.TryGetValue(orderId, out order);
    }

    private static IEnumerable<OrderStatus> SeedData() =>
    [
        new OrderStatus(
            "ORD-1001",
            "Contoso Retail",
            "Shipped",
            "Northwind Freight",
            "NF-88421156",
            new DateOnly(2026, 7, 2),
            new DateTimeOffset(2026, 6, 26, 8, 30, 0, TimeSpan.Zero)),
        new OrderStatus(
            "ORD-1002",
            "Fabrikam Logistics",
            "Processing",
            null,
            null,
            new DateOnly(2026, 7, 9),
            new DateTimeOffset(2026, 6, 25, 14, 5, 0, TimeSpan.Zero)),
        new OrderStatus(
            "ORD-1003",
            "Tailwind Traders",
            "Delivered",
            "Adventure Works Courier",
            "AWC-20260620-7741",
            new DateOnly(2026, 6, 24),
            new DateTimeOffset(2026, 6, 24, 17, 45, 0, TimeSpan.Zero)),
    ];
}
