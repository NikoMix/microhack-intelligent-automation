namespace IAuto.HybridIntegration.OnPremStub.Models;

/// <summary>
/// A read-only projection of an order as exposed by the (simulated) on-prem line-of-business
/// system. In the real migration story this is a SOAP/REST endpoint reached over a hybrid
/// connection (VNet, ER, or the Logic Apps on-premises data gateway).
/// </summary>
/// <param name="OrderId">Stable business identifier of the order.</param>
/// <param name="Customer">Display name of the customer who placed the order.</param>
/// <param name="Status">Fulfilment status, e.g. <c>Processing</c>, <c>Shipped</c>, <c>Delivered</c>.</param>
/// <param name="Carrier">Shipping carrier handling the order, when dispatched.</param>
/// <param name="TrackingNumber">Carrier tracking number, when dispatched.</param>
/// <param name="EstimatedDelivery">Estimated delivery date in ISO-8601 (date only), when known.</param>
/// <param name="LastUpdatedUtc">Timestamp of the last status change, in UTC.</param>
public sealed record OrderStatus(
    string OrderId,
    string Customer,
    string Status,
    string? Carrier,
    string? TrackingNumber,
    DateOnly? EstimatedDelivery,
    DateTimeOffset LastUpdatedUtc);
