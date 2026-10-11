using System.Globalization;
using IAuto.DocumentProcessing.Models;

namespace IAuto.DocumentProcessing.DocumentIntelligence;

public sealed class InvoiceFieldMapper : IInvoiceFieldMapper
{
    public InvoiceAnalysis Map(RawInvoiceDocument document)
    {
        ArgumentNullException.ThrowIfNull(document);

        var fields = document.Fields;
        var total = GetCurrency(fields, "InvoiceTotal") ?? GetCurrency(fields, "AmountDue") ?? GetDecimal(fields, "Total");
        var currencyCode = GetCurrencyCode(fields, "InvoiceTotal") ?? GetCurrencyCode(fields, "AmountDue");

        return new InvoiceAnalysis(
            VendorName: GetText(fields, "VendorName") ?? GetText(fields, "VendorAddressRecipient"),
            InvoiceId: GetText(fields, "InvoiceId"),
            InvoiceDate: GetDate(fields, "InvoiceDate"),
            CurrencyCode: currencyCode,
            Total: total,
            LineItems: GetLineItems(fields),
            OverallConfidence: document.Confidence ?? AverageConfidence(fields.Values));
    }

    private static IReadOnlyList<InvoiceLineItem> GetLineItems(IReadOnlyDictionary<string, RawInvoiceField> fields)
    {
        if (!fields.TryGetValue("Items", out var itemsField) || itemsField.ArrayValue is not { Count: > 0 } items)
        {
            return [];
        }

        var result = new List<InvoiceLineItem>(items.Count);
        foreach (var item in items)
        {
            if (item.ObjectValue is not { Count: > 0 } values)
            {
                continue;
            }

            result.Add(new InvoiceLineItem(
                Description: GetText(values, "Description"),
                Quantity: GetDecimal(values, "Quantity"),
                UnitPrice: GetCurrency(values, "UnitPrice") ?? GetDecimal(values, "UnitPrice"),
                Amount: GetCurrency(values, "Amount") ?? GetDecimal(values, "Amount")));
        }

        return result;
    }

    private static string? GetText(IReadOnlyDictionary<string, RawInvoiceField> fields, string name)
    {
        if (!fields.TryGetValue(name, out var field))
        {
            return null;
        }

        return FirstNonWhiteSpace(field.StringValue, field.Content);
    }

    private static DateOnly? GetDate(IReadOnlyDictionary<string, RawInvoiceField> fields, string name)
    {
        if (!fields.TryGetValue(name, out var field))
        {
            return null;
        }

        if (field.DateValue is { } date)
        {
            return date;
        }

        var raw = FirstNonWhiteSpace(field.StringValue, field.Content);
        return DateOnly.TryParse(raw, CultureInfo.InvariantCulture, DateTimeStyles.None, out var parsed) ? parsed : null;
    }

    private static decimal? GetCurrency(IReadOnlyDictionary<string, RawInvoiceField> fields, string name) =>
        fields.TryGetValue(name, out var field) ? field.CurrencyAmount ?? field.NumberValue ?? ParseDecimal(field.StringValue ?? field.Content) : null;

    private static string? GetCurrencyCode(IReadOnlyDictionary<string, RawInvoiceField> fields, string name) =>
        fields.TryGetValue(name, out var field) ? FirstNonWhiteSpace(field.CurrencyCode) : null;

    private static decimal? GetDecimal(IReadOnlyDictionary<string, RawInvoiceField> fields, string name) =>
        fields.TryGetValue(name, out var field) ? field.NumberValue ?? field.CurrencyAmount ?? ParseDecimal(field.StringValue ?? field.Content) : null;

    private static decimal? ParseDecimal(string? raw)
    {
        if (string.IsNullOrWhiteSpace(raw))
        {
            return null;
        }

        var normalized = raw.Replace("$", string.Empty, StringComparison.Ordinal)
            .Replace("€", string.Empty, StringComparison.Ordinal)
            .Replace(",", string.Empty, StringComparison.Ordinal)
            .Trim();

        return decimal.TryParse(normalized, NumberStyles.Number | NumberStyles.AllowCurrencySymbol, CultureInfo.InvariantCulture, out var parsed)
            ? parsed
            : null;
    }

    private static string? FirstNonWhiteSpace(params string?[] values) =>
        values.FirstOrDefault(value => !string.IsNullOrWhiteSpace(value))?.Trim();

    private static double? AverageConfidence(IEnumerable<RawInvoiceField> fields)
    {
        var confidenceValues = fields.Select(f => f.Confidence).Where(v => v.HasValue).Select(v => v!.Value).ToArray();
        return confidenceValues.Length == 0 ? null : confidenceValues.Average();
    }
}
