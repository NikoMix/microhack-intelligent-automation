using Azure.Core;
using Azure.Identity;
using Azure.Storage.Blobs;
using IAuto.DocumentProcessing.Configuration;
using IAuto.DocumentProcessing.DocumentIntelligence;
using IAuto.DocumentProcessing.Inference;
using IAuto.DocumentProcessing.Storage;
using IAuto.Inference;
using Microsoft.Azure.Functions.Worker;
using Microsoft.Azure.Functions.Worker.ApplicationInsights;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;

var host = new HostBuilder()
    .ConfigureFunctionsWorkerDefaults()
    .ConfigureServices(services =>
    {
        services
            .AddApplicationInsightsTelemetryWorkerService()
            .ConfigureFunctionsApplicationInsights();

        services
            .AddOptions<DocumentProcessingOptions>()
            .BindConfiguration(DocumentProcessingOptions.SectionName)
            .ValidateDataAnnotations()
            .ValidateOnStart();

        services.AddSingleton<TokenCredential, DefaultAzureCredential>();
        services.AddSingleton<IDocumentInvoiceAnalyzer, AzureDocumentInvoiceAnalyzer>();
        services.AddSingleton<IInvoiceFieldMapper, InvoiceFieldMapper>();
        services.AddSingleton<IInvoiceSummarizer, InferenceInvoiceSummarizer>();
        services.AddSingleton<IInvoiceSummaryInference, ModularInferenceSummaryClient>();
        services.AddSingleton<IProcessedInvoiceWriter, BlobProcessedInvoiceWriter>();
        services.AddSingleton(sp =>
        {
            var options = sp.GetRequiredService<Microsoft.Extensions.Options.IOptions<DocumentProcessingOptions>>().Value;
            var credential = sp.GetRequiredService<TokenCredential>();
            return new BlobServiceClient(new Uri(options.StorageBlobServiceUri), credential);
        });
        services.AddModularInference();
    })
    .Build();

await host.RunAsync().ConfigureAwait(false);
