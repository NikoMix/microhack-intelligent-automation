namespace IAuto.DocumentProcessing.DocumentIntelligence;

public sealed record RawInvoiceField(
    string? Content = null,
    string? StringValue = null,
    decimal? NumberValue = null,
    DateOnly? DateValue = null,
    decimal? CurrencyAmount = null,
    string? CurrencyCode = null,
    double? Confidence = null,
    IReadOnlyDictionary<string, RawInvoiceField>? ObjectValue = null,
    IReadOnlyList<RawInvoiceField>? ArrayValue = null);
