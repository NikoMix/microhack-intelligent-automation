using System.Text.Json.Serialization;

namespace IAuto.HybridIntegration.Functions.Models;

/// <summary>Business event formerly submitted by a Power Automate flow through an on-premises data gateway.</summary>
public sealed record BusinessEventRequest
{
    /// <summary>Caller-supplied event identifier. A deterministic value is generated when omitted.</summary>
    [JsonPropertyName("eventId")]
    public string? EventId { get; init; }

    /// <summary>Business event type, such as order.created or approval.requested.</summary>
    [JsonPropertyName("eventType")]
    public string EventType { get; init; } = string.Empty;

    /// <summary>Source system name, for example dynamics, sap, or power-automate.</summary>
    [JsonPropertyName("sourceSystem")]
    public string SourceSystem { get; init; } = "power-automate";

    /// <summary>Customer or partner identifier associated with the event.</summary>
    [JsonPropertyName("customerId")]
    public string? CustomerId { get; init; }

    /// <summary>Monetary value that drives the approval routing example.</summary>
    [JsonPropertyName("amount")]
    public decimal Amount { get; init; }

    /// <summary>ISO currency code for <see cref="Amount"/>.</summary>
    [JsonPropertyName("currency")]
    public string Currency { get; init; } = "USD";

    /// <summary>Optional URL to the original approval item or business record.</summary>
    [JsonPropertyName("approvalUrl")]
    public string? ApprovalUrl { get; init; }

    /// <summary>Additional non-sensitive metadata forwarded from the legacy automation.</summary>
    [JsonPropertyName("metadata")]
    public IReadOnlyDictionary<string, string>? Metadata { get; init; }
}
