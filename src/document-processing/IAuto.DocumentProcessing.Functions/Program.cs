using Azure.Monitor.OpenTelemetry.Exporter;
using IAuto.DocumentProcessing.DependencyInjection;
using IAuto.DocumentProcessing.Telemetry;
using Microsoft.Azure.Functions.Worker.Builder;
using Microsoft.Azure.Functions.Worker.OpenTelemetry;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using OpenTelemetry;
using OpenTelemetry.Metrics;
using OpenTelemetry.Trace;

FunctionsApplicationBuilder builder = FunctionsApplication.CreateBuilder(args);

builder.ConfigureFunctionsWebApplication();

// OpenTelemetry: capture the Functions worker defaults plus the pipeline's own
// ActivitySource and Meter. Export to Azure Monitor only when configured so local runs
// (no Application Insights) work out of the box. host.json sets telemetryMode=OpenTelemetry.
IOpenTelemetryBuilder otel = builder.Services.AddOpenTelemetry()
    .UseFunctionsWorkerDefaults()
    .WithTracing(tracing => tracing.AddSource(DocumentProcessingDiagnostics.SourceName))
    .WithMetrics(metrics => metrics.AddMeter(DocumentProcessingDiagnostics.SourceName));

if (!string.IsNullOrWhiteSpace(builder.Configuration["APPLICATIONINSIGHTS_CONNECTION_STRING"]))
{
    otel.UseAzureMonitorExporter();
}

// Register the document-processing pipeline (analyzer, optional modular-inference insights,
// human-in-the-loop approval queue) from configuration.
builder.Services.AddDocumentProcessing(builder.Configuration);

builder.Build().Run();
