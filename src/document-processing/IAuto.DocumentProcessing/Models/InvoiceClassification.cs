namespace IAuto.DocumentProcessing.Models;

public sealed record InvoiceClassification(
    string Category,
    string Risk,
    string Rationale);
