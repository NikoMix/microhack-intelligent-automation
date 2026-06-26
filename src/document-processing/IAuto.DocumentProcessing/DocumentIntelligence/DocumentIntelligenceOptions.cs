namespace IAuto.DocumentProcessing.DocumentIntelligence;

/// <summary>Binds the <c>DocumentIntelligence</c> configuration section.</summary>
public sealed class DocumentIntelligenceOptions
{
    /// <summary>Configuration section name.</summary>
    public const string SectionName = "DocumentIntelligence";

    /// <summary>Document Intelligence resource endpoint.</summary>
    public string? Endpoint { get; set; }

    /// <summary>Optional API key. When empty, Entra ID (DefaultAzureCredential) is used.</summary>
    public string? ApiKey { get; set; }
}
