using Microsoft.Extensions.Logging;

namespace IAuto.DocumentProcessing;

/// <summary>High-performance source-generated log messages for the pipeline.</summary>
internal static partial class Log
{
    [LoggerMessage(
        EventId = 1000,
        Level = LogLevel.Information,
        Message = "Analyzing document {DocumentName} with model {ModelId}.")]
    public static partial void AnalyzingDocument(ILogger logger, string documentName, string modelId);

    [LoggerMessage(
        EventId = 1001,
        Level = LogLevel.Information,
        Message = "Analyzed document {DocumentName}: {FieldCount} fields, overall confidence {Confidence}.")]
    public static partial void AnalyzedDocument(
        ILogger logger,
        string documentName,
        int fieldCount,
        double confidence);

    [LoggerMessage(
        EventId = 1002,
        Level = LogLevel.Information,
        Message = "Document {DocumentName} auto-approved.")]
    public static partial void AutoApproved(ILogger logger, string documentName);

    [LoggerMessage(
        EventId = 1003,
        Level = LogLevel.Information,
        Message = "Document {DocumentName} routed for review (approval {ApprovalReference}).")]
    public static partial void PendingReview(ILogger logger, string documentName, string approvalReference);

    [LoggerMessage(
        EventId = 1004,
        Level = LogLevel.Error,
        Message = "Processing failed for document {DocumentName}.")]
    public static partial void ProcessingFailed(ILogger logger, string documentName, Exception exception);

    [LoggerMessage(
        EventId = 1005,
        Level = LogLevel.Warning,
        Message = "Insight generation failed; continuing without insights.")]
    public static partial void InsightGenerationFailed(ILogger logger, Exception exception);

    [LoggerMessage(
        EventId = 1006,
        Level = LogLevel.Information,
        Message = "Enqueued approval for document {DocumentName} as {ApprovalReference}.")]
    public static partial void EnqueuedApproval(ILogger logger, string documentName, string approvalReference);
}
