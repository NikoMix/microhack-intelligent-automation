using System.Globalization;
using Azure.AI.DocumentIntelligence;
using IAuto.DocumentProcessing.DocumentIntelligence;
using IAuto.DocumentProcessing.Models;

namespace IAuto.DocumentProcessing.Tests;

/// <summary>
/// Tests the SDK-to-domain mapper using <see cref="DocumentIntelligenceModelFactory"/> so no
/// network or live Document Intelligence resource is required.
/// </summary>
public sealed class DocumentResultMapperTests
{
    private static DocumentField Field(
        DocumentFieldType type,
        string? valueString = null,
        double? valueDouble = null,
        long? valueInt64 = null,
        DateTimeOffset? valueDate = null,
        CurrencyValue? valueCurrency = null,
        string? content = null,
        float? confidence = null) =>
        DocumentIntelligenceModelFactory.DocumentField(
            fieldType: type,
            valueString: valueString!,
            valueDouble: valueDouble,
            valueInt64: valueInt64,
            valueDate: valueDate,
            valueCurrency: valueCurrency!,
            content: content!,
            confidence: confidence);

    private static AnalyzeResult ResultWithDocument(
        string content,
        float docConfidence,
        IReadOnlyDictionary<string, DocumentField> fields)
    {
        AnalyzedDocument document = DocumentIntelligenceModelFactory.AnalyzedDocument(
            documentType: "invoice",
            fields: DocumentIntelligenceModelFactory.DocumentFieldDictionary(fields),
            confidence: docConfidence);

        return DocumentIntelligenceModelFactory.AnalyzeResult(
            modelId: "prebuilt-invoice",
            content: content,
            documents: [document]);
    }

    [Fact]
    public void Map_MapsFields_AndPrefersDocumentConfidence()
    {
        var fields = new Dictionary<string, DocumentField>(StringComparer.Ordinal)
        {
            ["VendorName"] = Field(DocumentFieldType.String, valueString: "ACME", confidence: 0.97f),
            ["InvoiceTotal"] = Field(
                DocumentFieldType.Currency,
                valueCurrency: DocumentIntelligenceModelFactory.CurrencyValue(100.5, "$", "USD"),
                confidence: 0.91f),
        };
        AnalyzeResult result = ResultWithDocument("INVOICE", 0.88f, fields);

        DocumentExtractionResult mapped = DocumentResultMapper.Map("prebuilt-invoice", result);

        Assert.Equal("prebuilt-invoice", mapped.ModelId);
        Assert.Equal("INVOICE", mapped.Content);
        Assert.NotNull(mapped.OverallConfidence);
        Assert.Equal(0.88, mapped.OverallConfidence!.Value, 3);

        Dictionary<string, ExtractedField> byName = mapped.Fields.ToDictionary(f => f.Name, StringComparer.Ordinal);
        Assert.Equal("ACME", byName["VendorName"].Value);
        Assert.Equal("string", byName["VendorName"].FieldType);
        Assert.Equal("$100.5", byName["InvoiceTotal"].Value);
        Assert.Equal("currency", byName["InvoiceTotal"].FieldType);
    }

    [Fact]
    public void Map_FormatsValues_ByFieldType()
    {
        var invoiceDate = new DateTimeOffset(2026, 1, 15, 0, 0, 0, TimeSpan.Zero);
        var fields = new Dictionary<string, DocumentField>(StringComparer.Ordinal)
        {
            ["Amount"] = Field(DocumentFieldType.Double, valueDouble: 42.25, confidence: 0.9f),
            ["Quantity"] = Field(DocumentFieldType.Int64, valueInt64: 7, confidence: 0.9f),
            ["InvoiceDate"] = Field(DocumentFieldType.Date, valueDate: invoiceDate, confidence: 0.9f),
            ["BillTo"] = Field(DocumentFieldType.Address, content: "1 Main St", confidence: 0.9f),
        };
        AnalyzeResult result = ResultWithDocument(string.Empty, 0.95f, fields);

        DocumentExtractionResult mapped = DocumentResultMapper.Map("prebuilt-invoice", result);
        Dictionary<string, string?> byName = mapped.Fields.ToDictionary(f => f.Name, f => f.Value, StringComparer.Ordinal);

        Assert.Equal("42.25", byName["Amount"]);
        Assert.Equal("7", byName["Quantity"]);
        Assert.Equal(invoiceDate.ToString("O", CultureInfo.InvariantCulture), byName["InvoiceDate"]);
        Assert.Equal("1 Main St", byName["BillTo"]);
    }

    [Fact]
    public void Map_ReturnsNullConfidence_AndNoFields_WhenNoDocuments()
    {
        AnalyzeResult result = DocumentIntelligenceModelFactory.AnalyzeResult(
            modelId: "prebuilt-layout",
            content: "LAYOUT ONLY");

        DocumentExtractionResult mapped = DocumentResultMapper.Map("prebuilt-layout", result);

        Assert.Null(mapped.OverallConfidence);
        Assert.Empty(mapped.Fields);
        Assert.Equal("LAYOUT ONLY", mapped.Content);
        Assert.Equal(0, mapped.PageCount);
    }

    [Fact]
    public void Map_Throws_WhenModelIdMissing()
    {
        AnalyzeResult result = DocumentIntelligenceModelFactory.AnalyzeResult(modelId: "prebuilt-invoice");

        Assert.Throws<ArgumentException>(() => DocumentResultMapper.Map(" ", result));
    }
}
