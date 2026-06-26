using System.Diagnostics;
using System.Diagnostics.Metrics;

namespace IAuto.DocumentProcessing.Telemetry;

/// <summary>
/// Central <see cref="ActivitySource"/> and metrics for the document pipeline. Register the
/// source and meter name (<see cref="SourceName"/>) with OpenTelemetry in the host.
/// </summary>
public static class DocumentProcessingDiagnostics
{
    /// <summary>Logical name for tracing and metrics instrumentation.</summary>
    public const string SourceName = "IAuto.DocumentProcessing";

    private static readonly Meter Meter = new(SourceName);

    private static readonly Counter<long> AutoApprovedCounter =
        Meter.CreateCounter<long>("documents.auto_approved", description: "Documents auto-approved.");

    private static readonly Counter<long> PendingReviewCounter =
        Meter.CreateCounter<long>("documents.pending_review", description: "Documents routed for human review.");

    private static readonly Counter<long> FailedCounter =
        Meter.CreateCounter<long>("documents.failed", description: "Documents that failed processing.");

    /// <summary>Shared activity source for pipeline spans.</summary>
    public static ActivitySource ActivitySource { get; } = new(SourceName);

    /// <summary>Increment the auto-approved counter.</summary>
    public static void RecordAutoApproved() => AutoApprovedCounter.Add(1);

    /// <summary>Increment the pending-review counter.</summary>
    public static void RecordPendingReview() => PendingReviewCounter.Add(1);

    /// <summary>Increment the failed counter.</summary>
    public static void RecordFailed() => FailedCounter.Add(1);
}
