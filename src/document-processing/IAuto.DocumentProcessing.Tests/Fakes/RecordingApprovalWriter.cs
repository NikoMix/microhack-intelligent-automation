using IAuto.DocumentProcessing.Abstractions;
using IAuto.DocumentProcessing.Models;

namespace IAuto.DocumentProcessing.Tests.Fakes;

/// <summary><see cref="IApprovalQueueWriter"/> that records the last request instead of using a queue.</summary>
internal sealed class RecordingApprovalWriter : IApprovalQueueWriter
{
    public ApprovalRequest? LastRequest { get; private set; }

    public int CallCount { get; private set; }

    public string ReturnId { get; set; } = "approval-123";

    public Task<string> EnqueueAsync(ApprovalRequest request, CancellationToken cancellationToken = default)
    {
        LastRequest = request;
        CallCount++;
        return Task.FromResult(ReturnId);
    }
}
