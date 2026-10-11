namespace IAuto.DocumentProcessing.DocumentIntelligence;

public sealed record RawInvoiceDocument(
    IReadOnlyDictionary<string, RawInvoiceField> Fields,
    double? Confidence);
