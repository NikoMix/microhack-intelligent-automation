using Azure;
using Azure.AI.DocumentIntelligence;
using Azure.Core;
using Azure.Identity;
using Azure.Storage.Queues;
using IAuto.DocumentProcessing.Abstractions;
using IAuto.DocumentProcessing.DocumentIntelligence;
using IAuto.DocumentProcessing.HumanInTheLoop;
using IAuto.DocumentProcessing.Insights;
using IAuto.DocumentProcessing.Pipeline;
using IAuto.Inference;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.DependencyInjection.Extensions;
using Microsoft.Extensions.Options;

namespace IAuto.DocumentProcessing.DependencyInjection;

/// <summary>Registers the document-processing pipeline and its dependencies.</summary>
public static class DocumentProcessingServiceCollectionExtensions
{
    /// <summary>
    /// Register the full document-processing pipeline: the Document Intelligence analyzer,
    /// optional modular-inference insights, the human-in-the-loop approval queue, and the
    /// orchestrating pipeline. Authentication prefers Entra ID via
    /// <see cref="DefaultAzureCredential"/>, with key and connection-string fallbacks for
    /// classroom use.
    /// </summary>
    /// <param name="services">The service collection.</param>
    /// <param name="configuration">Configuration root supplying the bound sections.</param>
    /// <returns>The same service collection for chaining.</returns>
    public static IServiceCollection AddDocumentProcessing(
        this IServiceCollection services,
        IConfiguration configuration)
    {
        ArgumentNullException.ThrowIfNull(services);
        ArgumentNullException.ThrowIfNull(configuration);

        services.AddOptions<DocumentProcessingOptions>()
            .Bind(configuration.GetSection(DocumentProcessingOptions.SectionName));
        services.AddOptions<DocumentIntelligenceOptions>()
            .Bind(configuration.GetSection(DocumentIntelligenceOptions.SectionName));
        services.AddOptions<ApprovalQueueOptions>()
            .Bind(configuration.GetSection(ApprovalQueueOptions.SectionName));

        services.TryAddSingleton<TokenCredential>(new DefaultAzureCredential());
        services.TryAddSingleton(TimeProvider.System);

        services.AddSingleton(CreateDocumentIntelligenceClient);
        services.AddSingleton<IDocumentAnalyzer, DocumentIntelligenceAnalyzer>();

        services.AddSingleton(CreateQueueClient);
        services.AddSingleton<IApprovalQueueWriter, StorageQueueApprovalWriter>();

        IConfigurationSection processingSection =
            configuration.GetSection(DocumentProcessingOptions.SectionName);
        bool enableInsights =
            processingSection.GetValue<bool>(nameof(DocumentProcessingOptions.EnableInsights));
        if (enableInsights)
        {
            services.AddModularInference();
            services.AddSingleton<IDocumentInsightGenerator, ChatInsightGenerator>();
        }
        else
        {
            services.AddSingleton<IDocumentInsightGenerator, NullInsightGenerator>();
        }

        services.AddSingleton<IDocumentProcessingPipeline, DocumentProcessingPipeline>();
        return services;
    }

    private static DocumentIntelligenceClient CreateDocumentIntelligenceClient(IServiceProvider provider)
    {
        DocumentIntelligenceOptions options =
            provider.GetRequiredService<IOptions<DocumentIntelligenceOptions>>().Value;
        if (string.IsNullOrWhiteSpace(options.Endpoint))
        {
            throw new InvalidOperationException(
                "DocumentIntelligence:Endpoint is required. Set it in configuration or environment.");
        }

        var endpoint = new Uri(options.Endpoint);
        if (!string.IsNullOrWhiteSpace(options.ApiKey))
        {
            return new DocumentIntelligenceClient(endpoint, new AzureKeyCredential(options.ApiKey));
        }

        return new DocumentIntelligenceClient(endpoint, provider.GetRequiredService<TokenCredential>());
    }

    private static QueueClient CreateQueueClient(IServiceProvider provider)
    {
        ApprovalQueueOptions options =
            provider.GetRequiredService<IOptions<ApprovalQueueOptions>>().Value;
        var queueOptions = new QueueClientOptions { MessageEncoding = QueueMessageEncoding.None };

        if (!string.IsNullOrWhiteSpace(options.QueueServiceUri))
        {
            var queueUri = new Uri($"{options.QueueServiceUri.TrimEnd('/')}/{options.QueueName}");
            return new QueueClient(queueUri, provider.GetRequiredService<TokenCredential>(), queueOptions);
        }

        if (!string.IsNullOrWhiteSpace(options.ConnectionString))
        {
            return new QueueClient(options.ConnectionString, options.QueueName, queueOptions);
        }

        throw new InvalidOperationException(
            "Approval:QueueServiceUri or Approval:ConnectionString must be configured.");
    }
}
