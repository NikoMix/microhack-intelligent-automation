using System.Text.Json;
using Azure.Storage.Queues;
using IAuto.DocumentProcessing.Abstractions;
using IAuto.DocumentProcessing.Models;
using Microsoft.Extensions.Logging;

namespace IAuto.DocumentProcessing.HumanInTheLoop;

/// <summary>
/// <see cref="IApprovalQueueWriter"/> backed by an Azure Storage Queue. Serializes a versioned
/// <see cref="ApprovalEnvelope"/> as JSON so a downstream reviewer experience (Logic App,
/// Teams, a small web app) can render and act on it.
/// </summary>
public sealed class StorageQueueApprovalWriter : IApprovalQueueWriter
{
    private static readonly JsonSerializerOptions SerializerOptions = new(JsonSerializerDefaults.Web);

    private readonly QueueClient _queueClient;
    private readonly TimeProvider _timeProvider;
    private readonly ILogger<StorageQueueApprovalWriter> _logger;

    /// <summary>Create the queue adapter.</summary>
    /// <param name="queueClient">Azure Storage queue client.</param>
    /// <param name="timeProvider">Clock used for envelope timestamps (injected for testability).</param>
    /// <param name="logger">Logger for diagnostics.</param>
    public StorageQueueApprovalWriter(
        QueueClient queueClient,
        TimeProvider timeProvider,
        ILogger<StorageQueueApprovalWriter> logger)
    {
        ArgumentNullException.ThrowIfNull(queueClient);
        ArgumentNullException.ThrowIfNull(timeProvider);
        ArgumentNullException.ThrowIfNull(logger);
        _queueClient = queueClient;
        _timeProvider = timeProvider;
        _logger = logger;
    }

    /// <inheritdoc />
    public async Task<string> EnqueueAsync(
        ApprovalRequest request,
        CancellationToken cancellationToken = default)
    {
        ArgumentNullException.ThrowIfNull(request);

        ApprovalEnvelope envelope = CreateEnvelope(request, _timeProvider.GetUtcNow());
        string payload = Serialize(envelope);

        await _queueClient.CreateIfNotExistsAsync(cancellationToken: cancellationToken).ConfigureAwait(false);
        await _queueClient.SendMessageAsync(payload, cancellationToken).ConfigureAwait(false);

        Log.EnqueuedApproval(_logger, request.DocumentName, envelope.Id);
        return envelope.Id;
    }

    /// <summary>Build a versioned approval envelope. Exposed for unit testing the payload shape.</summary>
    /// <param name="request">The review payload.</param>
    /// <param name="createdAt">Creation timestamp.</param>
    /// <returns>The envelope to enqueue.</returns>
    public static ApprovalEnvelope CreateEnvelope(ApprovalRequest request, DateTimeOffset createdAt)
    {
        ArgumentNullException.ThrowIfNull(request);
        return new ApprovalEnvelope
        {
            Id = Guid.NewGuid().ToString("N"),
            CreatedAt = createdAt,
            Request = request,
        };
    }

    /// <summary>Serialize an envelope to the JSON written to the queue.</summary>
    /// <param name="envelope">The envelope to serialize.</param>
    /// <returns>The JSON payload.</returns>
    public static string Serialize(ApprovalEnvelope envelope) =>
        JsonSerializer.Serialize(envelope, SerializerOptions);
}
