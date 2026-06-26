using IAuto.DocumentProcessing.Models;
using Microsoft.Extensions.Logging;

namespace IAuto.DocumentProcessing.Functions;

/// <summary>High-performance source-generated log messages for the Functions host.</summary>
internal static partial class Log
{
    [LoggerMessage(
        EventId = 2000,
        Level = LogLevel.Information,
        Message = "Blob trigger received {BlobName} ({ByteCount} bytes).")]
    public static partial void BlobReceived(ILogger logger, string blobName, int byteCount);

    [LoggerMessage(
        EventId = 2001,
        Level = LogLevel.Information,
        Message = "Document {DocumentName} processed with status {Status}.")]
    public static partial void DocumentProcessed(
        ILogger logger,
        string documentName,
        DocumentProcessingStatus status);

    [LoggerMessage(
        EventId = 2002,
        Level = LogLevel.Information,
        Message = "HTTP trigger received request for {DocumentName} (model {ModelId}).")]
    public static partial void HttpReceived(ILogger logger, string documentName, string modelId);

    [LoggerMessage(
        EventId = 2003,
        Level = LogLevel.Warning,
        Message = "HTTP request rejected: {Reason}.")]
    public static partial void HttpRejected(ILogger logger, string reason);

    [LoggerMessage(
        EventId = 2004,
        Level = LogLevel.Information,
        Message = "Review notification for approval {ApprovalId}: document {DocumentName} needs human review.")]
    public static partial void ReviewNotification(ILogger logger, string approvalId, string documentName);

    [LoggerMessage(
        EventId = 2005,
        Level = LogLevel.Warning,
        Message = "Could not deserialize approval message from the review queue; skipping.")]
    public static partial void ReviewMessageInvalid(ILogger logger);
}
