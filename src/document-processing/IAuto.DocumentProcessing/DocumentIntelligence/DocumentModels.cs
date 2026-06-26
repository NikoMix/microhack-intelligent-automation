namespace IAuto.DocumentProcessing.DocumentIntelligence;

/// <summary>Well-known Azure AI Document Intelligence prebuilt model identifiers.</summary>
/// <remarks>
/// Custom models are referenced by their training model id; pass it via
/// <see cref="Models.DocumentAnalysisRequest.ModelId"/> or the configured default.
/// </remarks>
public static class DocumentModels
{
    /// <summary>Layout model: text, tables, and structure with no typed fields.</summary>
    public const string Layout = "prebuilt-layout";

    /// <summary>General document model: key-value pairs and entities.</summary>
    public const string Document = "prebuilt-document";

    /// <summary>Invoice model: typed invoice fields (totals, vendor, dates).</summary>
    public const string Invoice = "prebuilt-invoice";

    /// <summary>Receipt model: typed receipt fields.</summary>
    public const string Receipt = "prebuilt-receipt";

    /// <summary>Identity document model.</summary>
    public const string IdentityDocument = "prebuilt-idDocument";

    /// <summary>US W-2 tax form model.</summary>
    public const string TaxUsW2 = "prebuilt-tax.us.w2";
}
