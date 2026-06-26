using Azure.Monitor.OpenTelemetry.Exporter;
using IAuto.HybridIntegration.Functions.Services;
using IAuto.Inference;
using Microsoft.Azure.Functions.Worker;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using OpenTelemetry.Metrics;
using OpenTelemetry.Resources;
using OpenTelemetry.Trace;

var host = new HostBuilder()
    .ConfigureFunctionsWorkerDefaults()
    .ConfigureAppConfiguration(configuration => configuration.AddEnvironmentVariables())
    .ConfigureServices((context, services) =>
    {
        services
            .AddApplicationInsightsTelemetryWorkerService()
            .ConfigureFunctionsApplicationInsights();

        services.AddModularInference();
        services.AddSingleton<IInferenceGateway, ModularInferenceGateway>();
        services.AddSingleton<BusinessEventProcessor>();

        var appInsightsConnectionString = context.Configuration["APPLICATIONINSIGHTS_CONNECTION_STRING"];
        services
            .AddOpenTelemetry()
            .ConfigureResource(resource => resource.AddService("iauto-hybrid-integration-bridge"))
            .WithTracing(tracing =>
            {
                tracing.AddSource(BusinessEventProcessor.ActivitySourceName);
                tracing.AddHttpClientInstrumentation();
                if (!string.IsNullOrWhiteSpace(appInsightsConnectionString))
                {
                    tracing.AddAzureMonitorTraceExporter(options => options.ConnectionString = appInsightsConnectionString);
                }
            })
            .WithMetrics(metrics =>
            {
                metrics.AddRuntimeInstrumentation();
                metrics.AddHttpClientInstrumentation();
                if (!string.IsNullOrWhiteSpace(appInsightsConnectionString))
                {
                    metrics.AddAzureMonitorMetricExporter(options => options.ConnectionString = appInsightsConnectionString);
                }
            });
    })
    .Build();

host.Run();
