namespace IAuto.DocumentProcessing.HumanInTheLoop;

/// <summary>Binds the <c>Approval</c> configuration section for the review queue.</summary>
public sealed class ApprovalQueueOptions
{
    /// <summary>Configuration section name.</summary>
    public const string SectionName = "Approval";

    /// <summary>
    /// Queue service URI for Entra ID auth, for example
    /// <c>https://account.queue.core.windows.net</c>.
    /// </summary>
    public string? QueueServiceUri { get; set; }

    /// <summary>Storage connection string fallback for local or classroom use.</summary>
    public string? ConnectionString { get; set; }

    /// <summary>Queue name for documents awaiting review.</summary>
    public string QueueName { get; set; } = "document-review";
}
