using System.Net;
using System.Net.Http.Json;
using System.Text.Json;
using IAuto.HybridIntegration.Connector.Models;
using Microsoft.Extensions.Logging;

namespace IAuto.HybridIntegration.Connector.Services;

/// <summary>
/// <see cref="IOnPremClient"/> backed by an <see cref="HttpClient"/>. In production the base
/// address points at the on-prem endpoint reached over a hybrid connection (VNet integration,
/// ExpressRoute, or the on-premises data gateway); in the lab it points at the local stub.
/// </summary>
public sealed partial class OnPremClient : IOnPremClient
{
    private static readonly JsonSerializerOptions SerializerOptions =
        new(JsonSerializerDefaults.Web);

    private readonly HttpClient _httpClient;
    private readonly ILogger<OnPremClient> _logger;

    /// <summary>Create the client over a configured (typed) <see cref="HttpClient"/>.</summary>
    /// <param name="httpClient">Typed client whose base address targets the on-prem system.</param>
    /// <param name="logger">Logger used for dependency telemetry.</param>
    public OnPremClient(HttpClient httpClient, ILogger<OnPremClient> logger)
    {
        _httpClient = httpClient ?? throw new ArgumentNullException(nameof(httpClient));
        _logger = logger ?? throw new ArgumentNullException(nameof(logger));
    }

    /// <inheritdoc />
    public async Task<OnPremOrder?> GetOrderAsync(
        string orderId,
        CancellationToken cancellationToken = default)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(orderId);

        var path = $"orders/{Uri.EscapeDataString(orderId)}";
        using var response = await _httpClient.GetAsync(path, cancellationToken).ConfigureAwait(false);

        if (response.StatusCode == HttpStatusCode.NotFound)
        {
            LogOrderNotFound(orderId);
            return null;
        }

        response.EnsureSuccessStatusCode();

        return await response.Content
            .ReadFromJsonAsync<OnPremOrder>(SerializerOptions, cancellationToken)
            .ConfigureAwait(false);
    }

    [LoggerMessage(Level = LogLevel.Information, Message = "On-prem order {OrderId} not found.")]
    private partial void LogOrderNotFound(string orderId);
}
