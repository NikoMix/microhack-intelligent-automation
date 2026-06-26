using System.Globalization;
using IAuto.HybridIntegration.Connector.Models;
using IAuto.Inference;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.Logging;

namespace IAuto.HybridIntegration.Connector.Services;

/// <summary>
/// Default <see cref="IOrderEnricher"/>. Fetches the order from on-prem, grounds a prompt in
/// those facts, and asks the modular-inference <see cref="IChatClient"/> to answer. The model
/// is selected by configuration (GitHub Models, Azure OpenAI, or Azure AI Foundry) — this code
/// never references a concrete provider.
/// </summary>
public sealed partial class OrderEnricher : IOrderEnricher
{
    private const string SystemPrompt =
        "You are a concise customer-service assistant for an order-fulfilment team. " +
        "Answer the customer's question using ONLY the order facts provided. " +
        "If the facts do not contain the answer, say so plainly and suggest contacting support. " +
        "Keep the answer to at most three sentences and never invent tracking numbers or dates.";

    private readonly IChatClient _chatClient;
    private readonly IOnPremClient _onPremClient;
    private readonly InferenceOptions _options;
    private readonly ILogger<OrderEnricher> _logger;

    /// <summary>Create the enricher from its collaborators.</summary>
    /// <param name="chatClient">Provider-agnostic chat client from the shared inference layer.</param>
    /// <param name="onPremClient">Client for the on-prem order system.</param>
    /// <param name="options">Resolved inference options (used to report the active provider/model).</param>
    /// <param name="logger">Logger used for runtime telemetry.</param>
    public OrderEnricher(
        IChatClient chatClient,
        IOnPremClient onPremClient,
        InferenceOptions options,
        ILogger<OrderEnricher> logger)
    {
        _chatClient = chatClient ?? throw new ArgumentNullException(nameof(chatClient));
        _onPremClient = onPremClient ?? throw new ArgumentNullException(nameof(onPremClient));
        _options = options ?? throw new ArgumentNullException(nameof(options));
        _logger = logger ?? throw new ArgumentNullException(nameof(logger));
    }

    /// <inheritdoc />
    public async Task<EnrichmentResult> EnrichAsync(
        EnrichmentRequest request,
        CancellationToken cancellationToken = default)
    {
        ArgumentNullException.ThrowIfNull(request);
        ArgumentException.ThrowIfNullOrWhiteSpace(request.OrderId);
        ArgumentException.ThrowIfNullOrWhiteSpace(request.Question);

        var provider = ToWireName(_options.Provider);
        var order = await _onPremClient.GetOrderAsync(request.OrderId, cancellationToken).ConfigureAwait(false);

        if (order is null)
        {
            LogOrderNotFound(request.OrderId);
            return new EnrichmentResult
            {
                OrderId = request.OrderId,
                Found = false,
                Status = null,
                Answer = $"We could not find an order with id '{request.OrderId}'. " +
                         "Please double-check the number or contact support.",
                Provider = provider,
                Model = null,
            };
        }

        var prompt = BuildPrompt(order, request.Question);
        var answer = await _chatClient
            .CompleteTextAsync(prompt, SystemPrompt, cancellationToken)
            .ConfigureAwait(false);

        LogAnswered(order.OrderId, provider);

        return new EnrichmentResult
        {
            OrderId = order.OrderId,
            Found = true,
            Status = order.Status,
            Answer = answer.Trim(),
            Provider = provider,
            Model = ResolveModel(),
        };
    }

    private string? ResolveModel()
    {
        try
        {
            return _options.DefaultModel();
        }
        catch (InferenceConfigurationException)
        {
            // The client was already validated when built; treat a missing model id as unknown.
            return null;
        }
    }

    private static string BuildPrompt(OnPremOrder order, string question)
    {
        var facts = new List<string>(capacity: 6)
        {
            $"Order id: {order.OrderId}",
            $"Customer: {order.Customer}",
            $"Status: {order.Status}",
        };

        if (!string.IsNullOrWhiteSpace(order.Carrier))
        {
            facts.Add($"Carrier: {order.Carrier}");
        }

        if (!string.IsNullOrWhiteSpace(order.TrackingNumber))
        {
            facts.Add($"Tracking number: {order.TrackingNumber}");
        }

        if (order.EstimatedDelivery is { } eta)
        {
            facts.Add($"Estimated delivery: {eta.ToString("yyyy-MM-dd", CultureInfo.InvariantCulture)}");
        }

        facts.Add($"Last updated (UTC): {order.LastUpdatedUtc.ToString("u", CultureInfo.InvariantCulture)}");

        return $"""
            Order facts:
            {string.Join(Environment.NewLine, facts)}

            Customer question: {question}
            """;
    }

    private static string ToWireName(Provider provider) => provider switch
    {
        Provider.GitHub => "github",
        Provider.AzureOpenAI => "azure_openai",
        Provider.Foundry => "foundry",
        _ => throw new ArgumentOutOfRangeException(nameof(provider), provider, "Unknown provider."),
    };

    [LoggerMessage(
        Level = LogLevel.Information,
        Message = "Order {OrderId} not found in on-prem system; skipping inference.")]
    private partial void LogOrderNotFound(string orderId);

    [LoggerMessage(
        Level = LogLevel.Information,
        Message = "Answered question for order {OrderId} via provider {Provider}.")]
    private partial void LogAnswered(string orderId, string provider);
}
