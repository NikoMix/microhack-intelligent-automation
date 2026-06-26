using System.Text.Json.Serialization;

namespace IAuto.HybridIntegration.Connector.Models;

/// <summary>
/// Inbound request handled by the connector: the order to look up and the customer's
/// natural-language question to answer from that order's data.
/// </summary>
public sealed record EnrichmentRequest
{
    /// <summary>Business id of the order to resolve from the on-prem system.</summary>
    [JsonPropertyName("orderId")]
    public string OrderId { get; init; } = string.Empty;

    /// <summary>The customer's question, answered by the modular-inference model.</summary>
    [JsonPropertyName("question")]
    public string Question { get; init; } = string.Empty;
}
