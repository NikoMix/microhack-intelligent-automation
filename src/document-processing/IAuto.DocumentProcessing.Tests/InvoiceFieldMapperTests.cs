using System.Text.Json;
using IAuto.DocumentProcessing.DocumentIntelligence;
using Xunit;

namespace IAuto.DocumentProcessing.Tests;

public sealed class InvoiceFieldMapperTests
{
    private static readonly JsonSerializerOptions JsonOptions = new(JsonSerializerDefaults.Web);

    [Fact]
    public async Task Map_ConvertsDocumentIntelligenceInvoiceFieldsAsync()
    {
        await using var fixture = File.OpenRead(Path.Combine("Fixtures", "sample-invoice-analysis.json"));
        var raw = await JsonSerializer.DeserializeAsync<RawInvoiceDocument>(fixture, JsonOptions);
        Assert.NotNull(raw);

        var invoice = new InvoiceFieldMapper().Map(raw);

        Assert.Equal("Contoso Office Supplies", invoice.VendorName);
        Assert.Equal("INV-1007", invoice.InvoiceId);
        Assert.Equal(new DateOnly(2026, 6, 1), invoice.InvoiceDate);
        Assert.Equal("USD", invoice.CurrencyCode);
        Assert.Equal(1245.50m, invoice.Total);
        Assert.Equal(0.96, invoice.OverallConfidence);
        Assert.Collection(
            invoice.LineItems,
            item =>
            {
                Assert.Equal("Ergonomic keyboards", item.Description);
                Assert.Equal(5m, item.Quantity);
                Assert.Equal(89.50m, item.UnitPrice);
                Assert.Equal(447.50m, item.Amount);
            },
            item =>
            {
                Assert.Equal("Docking stations", item.Description);
                Assert.Equal(4m, item.Quantity);
                Assert.Equal(199.50m, item.UnitPrice);
                Assert.Equal(798.00m, item.Amount);
            });
    }

    [Fact]
    public void Map_FallsBackToContentWhenTypedValuesAreMissing()
    {
        var raw = new RawInvoiceDocument(
            new Dictionary<string, RawInvoiceField>
            {
                ["VendorAddressRecipient"] = new(Content: "Fabrikam Ltd."),
                ["InvoiceTotal"] = new(Content: "$2,001.25"),
                ["InvoiceDate"] = new(Content: "2026-06-15"),
            },
            Confidence: null);

        var invoice = new InvoiceFieldMapper().Map(raw);

        Assert.Equal("Fabrikam Ltd.", invoice.VendorName);
        Assert.Equal(2001.25m, invoice.Total);
        Assert.Equal(new DateOnly(2026, 6, 15), invoice.InvoiceDate);
        Assert.Empty(invoice.LineItems);
    }
}


