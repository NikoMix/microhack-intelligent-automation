using System.Globalization;
using IAuto.HybridIntegration.Functions.Models;
using IAuto.Inference;
using Microsoft.Extensions.AI;

namespace IAuto.HybridIntegration.Functions.Services;

internal sealed class ModularInferenceGateway(IChatClient chatClient, InferenceOptions options) : IInferenceGateway
{
    private const string SystemPrompt = "You enrich integration events during a Power Platform to Azure migration. Return one concise sentence for an operations team.";

    public async Task<EventEnrichment> EnrichAsync(BusinessEventRequest request, CancellationToken cancellationToken)
    {
        ArgumentNullException.ThrowIfNull(request);

        var prompt = string.Create(
            CultureInfo.InvariantCulture,
            $"Summarize this event for routing: type={request.EventType}; source={request.SourceSystem}; customer={request.CustomerId ?? "unknown"}; amount={request.Amount:0.##} {request.Currency}.");
        var summary = await chatClient.CompleteTextAsync(prompt, SystemPrompt, cancellationToken).ConfigureAwait(false);

        return new EventEnrichment
        {
            Summary = string.IsNullOrWhiteSpace(summary) ? "No enrichment returned by the configured model." : summary.Trim(),
            Model = options.DefaultModel(),
        };
    }
}
