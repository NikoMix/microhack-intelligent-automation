using System.Diagnostics;
using IAuto.DocumentProcessing.DocumentIntelligence;
using IAuto.DocumentProcessing.Inference;
using IAuto.DocumentProcessing.Models;
using IAuto.DocumentProcessing.Storage;
using Microsoft.Azure.Functions.Worker;
using Microsoft.Extensions.Logging;

namespace IAuto.DocumentProcessing.Functions;

public sealed class ProcessInvoiceFunction
{
    private readonly IDocumentInvoiceAnalyzer _analyzer;
    private readonly IInvoiceSummarizer _summarizer;
    private readonly IProcessedInvoiceWriter _writer;
    private readonly ILogger<ProcessInvoiceFunction> _logger;

    public ProcessInvoiceFunction(
        IDocumentInvoiceAnalyzer analyzer,
        IInvoiceSummarizer summarizer,
        IProcessedInvoiceWriter writer,
        ILogger<ProcessInvoiceFunction> logger)
    {
        _analyzer = analyzer ?? throw new ArgumentNullException(nameof(analyzer));
        _summarizer = summarizer ?? throw new ArgumentNullException(nameof(summarizer));
        _writer = writer ?? throw new ArgumentNullException(nameof(writer));
        _logger = logger ?? throw new ArgumentNullException(nameof(logger));
    }

    [Function(nameof(ProcessInvoiceFunction))]
    public async Task RunAsync(
        [BlobTrigger("%DocumentProcessing__IncomingContainer%/{name}", Connection = "DocumentStorage", Source = BlobTriggerSource.EventGrid)] Stream invoiceBlob,
        string name,
        FunctionContext context,
        CancellationToken cancellationToken)
    {
        ArgumentNullException.ThrowIfNull(invoiceBlob);
        ArgumentNullException.ThrowIfNull(context);
        ArgumentException.ThrowIfNullOrWhiteSpace(name);

        _logger.LogInformation("Processing invoice blob {BlobName} for invocation {InvocationId}.", name, context.InvocationId);

        var analysis = await _analyzer.AnalyzeInvoiceAsync(invoiceBlob, name, cancellationToken).ConfigureAwait(false);
        var summary = await _summarizer.SummarizeAsync(analysis, cancellationToken).ConfigureAwait(false);
        var processedBlobName = BuildProcessedBlobName(name);
        var telemetry = new ProcessingTelemetry(
            context.InvocationId,
            Activity.Current?.TraceId.ToString(),
            Activity.Current?.SpanId.ToString(),
            DateTimeOffset.UtcNow,
            nameof(ProcessInvoiceFunction));

        var result = new ProcessedInvoiceResult(
            name,
            processedBlobName,
            analysis,
            summary.Summary,
            summary.Classification,
            telemetry);

        await _writer.WriteAsync(result, cancellationToken).ConfigureAwait(false);

        _logger.LogInformation(
            "Processed invoice {BlobName} as {ProcessedBlobName}. Category={Category}, Risk={Risk}.",
            name,
            processedBlobName,
            result.Classification.Category,
            result.Classification.Risk);
    }

    private static string BuildProcessedBlobName(string sourceName)
    {
        var safeName = sourceName.Replace('\\', '/');
        var withoutExtension = Path.ChangeExtension(safeName, null);
        return $"{withoutExtension}.processed.json";
    }
}
