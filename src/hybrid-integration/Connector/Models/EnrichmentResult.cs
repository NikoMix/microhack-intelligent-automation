using System.Text.Json.Serialization;

namespace IAuto.HybridIntegration.Connector.Models;

/// <summary>
/// Result returned by the connector. Includes the AI answer plus the provider/model that
/// produced it, so the modular-inference backend in use is observable from the response.
/// </summary>
public sealed record EnrichmentResult
{
    /// <summary>The order id the request was for (echoed back).</summary>
    [JsonPropertyName("orderId")]
    public required string OrderId { get; init; }

    /// <summary>Whether the order was found in the on-prem system.</summary>
    [JsonPropertyName("found")]
    public bool Found { get; init; }

    /// <summary>The order's fulfilment status when found; otherwise <see langword="null"/>.</summary>
    [JsonPropertyName("status")]
    public string? Status { get; init; }

    /// <summary>The natural-language answer to the customer's question.</summary>
    [JsonPropertyName("answer")]
    public required string Answer { get; init; }

    /// <summary>The modular-inference provider that produced the answer (github | azure_openai | foundry).</summary>
    [JsonPropertyName("provider")]
    public required string Provider { get; init; }

    /// <summary>The model/deployment id that produced the answer, when known.</summary>
    [JsonPropertyName("model")]
    public string? Model { get; init; }
}
