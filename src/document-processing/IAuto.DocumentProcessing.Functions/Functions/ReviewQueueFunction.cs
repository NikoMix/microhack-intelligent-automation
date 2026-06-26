using System.Text.Json;
using IAuto.DocumentProcessing.Models;
using Microsoft.Azure.Functions.Worker;
using Microsoft.Extensions.Logging;

namespace IAuto.DocumentProcessing.Functions.Functions;

/// <summary>
/// Human-in-the-loop reviewer-notification stub. Triggers on the approval queue and logs the
/// notification a real reviewer experience (Logic App, Teams, or a small web app) would surface.
/// This keeps the lab buildable end to end without provisioning a full approval UI.
/// </summary>
public sealed class ReviewQueueFunction
{
    private static readonly JsonSerializerOptions SerializerOptions = new(JsonSerializerDefaults.Web);

    private readonly ILogger<ReviewQueueFunction> _logger;

    /// <summary>Create the review-queue function.</summary>
    /// <param name="logger">Logger for diagnostics.</param>
    public ReviewQueueFunction(ILogger<ReviewQueueFunction> logger)
    {
        ArgumentNullException.ThrowIfNull(logger);
        _logger = logger;
    }

    /// <summary>Handle a queued approval message by notifying a (stub) reviewer.</summary>
    /// <param name="message">Raw JSON envelope from the review queue.</param>
    [Function(nameof(ReviewQueueFunction))]
    public void Run(
        [QueueTrigger("%Approval:QueueName%", Connection = "Approval:Queue")] string message)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(message);

        ApprovalEnvelope? envelope = TryDeserialize(message);
        if (envelope is null)
        {
            Log.ReviewMessageInvalid(_logger);
            return;
        }

        Log.ReviewNotification(_logger, envelope.Id, envelope.Request.DocumentName);
    }

    private static ApprovalEnvelope? TryDeserialize(string message)
    {
        try
        {
            return JsonSerializer.Deserialize<ApprovalEnvelope>(message, SerializerOptions);
        }
        catch (JsonException)
        {
            return null;
        }
    }
}
