using System.Text.Json.Serialization;

namespace IAuto.HybridIntegration.Connector.Models;

/// <summary>
/// The connector's view of an order returned by the on-prem stub. Mirrors the stub's
/// <c>OrderStatus</c> contract; kept as a separate type so the two services stay decoupled.
/// </summary>
public sealed record OnPremOrder
{
    /// <summary>Business identifier of the order.</summary>
    [JsonPropertyName("orderId")]
    public string OrderId { get; init; } = string.Empty;

    /// <summary>Customer who placed the order.</summary>
    [JsonPropertyName("customer")]
    public string Customer { get; init; } = string.Empty;

    /// <summary>Fulfilment status (e.g. Processing, Shipped, Delivered).</summary>
    [JsonPropertyName("status")]
    public string Status { get; init; } = string.Empty;

    /// <summary>Shipping carrier, when dispatched.</summary>
    [JsonPropertyName("carrier")]
    public string? Carrier { get; init; }

    /// <summary>Carrier tracking number, when dispatched.</summary>
    [JsonPropertyName("trackingNumber")]
    public string? TrackingNumber { get; init; }

    /// <summary>Estimated delivery date, when known.</summary>
    [JsonPropertyName("estimatedDelivery")]
    public DateOnly? EstimatedDelivery { get; init; }

    /// <summary>Timestamp of the last status change, in UTC.</summary>
    [JsonPropertyName("lastUpdatedUtc")]
    public DateTimeOffset LastUpdatedUtc { get; init; }
}
