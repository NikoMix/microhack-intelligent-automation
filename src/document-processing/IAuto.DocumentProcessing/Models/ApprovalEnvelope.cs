namespace IAuto.DocumentProcessing.Models;

/// <summary>Versioned envelope wrapping an <see cref="ApprovalRequest"/> on the review queue.</summary>
public sealed record ApprovalEnvelope
{
    /// <summary>Stable schema version for forward-compatible consumers.</summary>
    public string SchemaVersion { get; init; } = "1.0";

    /// <summary>Unique id for the approval message.</summary>
    public required string Id { get; init; }

    /// <summary>UTC timestamp the approval was created.</summary>
    public required DateTimeOffset CreatedAt { get; init; }

    /// <summary>The review payload.</summary>
    public required ApprovalRequest Request { get; init; }
}
