using IAuto.DocumentProcessing.Models;

namespace IAuto.DocumentProcessing.Abstractions;

/// <summary>Enqueues documents that require human review (human-in-the-loop).</summary>
public interface IApprovalQueueWriter
{
    /// <summary>Enqueue an approval request and return the queued envelope's id.</summary>
    /// <param name="request">The review payload.</param>
    /// <param name="cancellationToken">Token to cancel the operation.</param>
    /// <returns>The id of the queued approval envelope.</returns>
    Task<string> EnqueueAsync(ApprovalRequest request, CancellationToken cancellationToken = default);
}
