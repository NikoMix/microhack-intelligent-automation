namespace IAuto.DocumentProcessing.Models;

public sealed record ProcessingTelemetry(
    string InvocationId,
    string? TraceId,
    string? SpanId,
    DateTimeOffset ProcessedAtUtc,
    string FunctionName);
