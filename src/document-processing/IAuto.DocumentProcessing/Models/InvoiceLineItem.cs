namespace IAuto.DocumentProcessing.Models;

public sealed record InvoiceLineItem(
    string? Description,
    decimal? Quantity,
    decimal? UnitPrice,
    decimal? Amount);
