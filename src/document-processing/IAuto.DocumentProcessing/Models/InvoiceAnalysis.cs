namespace IAuto.DocumentProcessing.Models;

public sealed record InvoiceAnalysis(
    string? VendorName,
    string? InvoiceId,
    DateOnly? InvoiceDate,
    string? CurrencyCode,
    decimal? Total,
    IReadOnlyList<InvoiceLineItem> LineItems,
    double? OverallConfidence);
