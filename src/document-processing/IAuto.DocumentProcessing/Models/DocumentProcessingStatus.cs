namespace IAuto.DocumentProcessing.Models;

/// <summary>Outcome of routing an analyzed document through the pipeline.</summary>
public enum DocumentProcessingStatus
{
    /// <summary>Extraction confidence cleared the threshold; no human review required.</summary>
    AutoApproved,

    /// <summary>Routed to a human for review (low confidence or missing required fields).</summary>
    PendingReview,

    /// <summary>Processing failed before a routing decision could be made.</summary>
    Failed,
}
