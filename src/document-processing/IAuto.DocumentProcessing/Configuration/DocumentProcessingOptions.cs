using System.ComponentModel.DataAnnotations;

namespace IAuto.DocumentProcessing.Configuration;

public sealed class DocumentProcessingOptions
{
    public const string SectionName = "DocumentProcessing";

    [Required]
    [Url]
    public string DocumentIntelligenceEndpoint { get; set; } = string.Empty;

    [Required]
    [Url]
    public string StorageBlobServiceUri { get; set; } = string.Empty;

    [Required]
    [RegularExpression("^[a-z0-9](?:[a-z0-9-]{1,61}[a-z0-9])$")]
    public string IncomingContainer { get; set; } = "incoming";

    [Required]
    [RegularExpression("^[a-z0-9](?:[a-z0-9-]{1,61}[a-z0-9])$")]
    public string ProcessedContainer { get; set; } = "processed";

    [Required]
    public string DocumentIntelligenceModelId { get; set; } = "prebuilt-invoice";
}
