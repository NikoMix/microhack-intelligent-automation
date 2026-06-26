using IAuto.DocumentProcessing.DocumentIntelligence;

namespace IAuto.DocumentProcessing.Pipeline;

/// <summary>Binds the <c>DocumentProcessing</c> configuration section that controls routing.</summary>
public sealed class DocumentProcessingOptions
{
    /// <summary>Configuration section name.</summary>
    public const string SectionName = "DocumentProcessing";

    /// <summary>Default Document Intelligence model id used when a request omits one.</summary>
    public string DefaultModelId { get; set; } = DocumentModels.Invoice;

    /// <summary>Minimum overall confidence (0–1) required to auto-approve.</summary>
    public double ConfidenceThreshold { get; set; } = 0.80;

    /// <summary>When <see langword="true"/>, generate LLM insights via modular inference.</summary>
    public bool EnableInsights { get; set; }

    /// <summary>Fields that must be present and non-empty to auto-approve.</summary>
    public IList<string> RequiredFields { get; } = [];

    /// <summary>Candidate categories offered to the insight model.</summary>
    public IList<string> InsightCategories { get; } = [];
}
