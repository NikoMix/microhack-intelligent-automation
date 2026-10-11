namespace IAuto.DocumentProcessing.Models;

public sealed record InvoiceSummaryResult(
    string Summary,
    InvoiceClassification Classification,
    string RawModelResponse);
