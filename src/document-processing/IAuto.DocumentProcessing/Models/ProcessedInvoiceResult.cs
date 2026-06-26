namespace IAuto.DocumentProcessing.Models;

public sealed record ProcessedInvoiceResult(
    string SourceBlobName,
    string ProcessedBlobName,
    InvoiceAnalysis ExtractedFields,
    string Summary,
    InvoiceClassification Classification,
    ProcessingTelemetry Telemetry);
