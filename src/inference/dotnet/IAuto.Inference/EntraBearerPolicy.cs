using System.ClientModel.Primitives;
using Azure.Core;

namespace IAuto.Inference;

/// <summary>
/// A <see cref="PipelinePolicy"/> that injects an Entra ID bearer token into outgoing
/// requests, enabling keyless authentication for the OpenAI SDK against Azure AI
/// Foundry. Tokens are cached and refreshed shortly before expiry.
/// </summary>
internal sealed class EntraBearerPolicy : PipelinePolicy
{
    private static readonly TimeSpan RefreshWindow = TimeSpan.FromMinutes(5);

    private readonly TokenCredential _credential;
    private readonly string[] _scopes;
    private readonly object _gate = new();
    private AccessToken _cached;

    public EntraBearerPolicy(TokenCredential credential, string scope)
    {
        _credential = credential ?? throw new ArgumentNullException(nameof(credential));
        _scopes = [scope];
    }

    public override void Process(
        PipelineMessage message,
        IReadOnlyList<PipelinePolicy> pipeline,
        int currentIndex)
    {
        ApplyToken(message, GetTokenSync());
        ProcessNext(message, pipeline, currentIndex);
    }

    public override async ValueTask ProcessAsync(
        PipelineMessage message,
        IReadOnlyList<PipelinePolicy> pipeline,
        int currentIndex)
    {
        ApplyToken(message, await GetTokenAsync().ConfigureAwait(false));
        await ProcessNextAsync(message, pipeline, currentIndex).ConfigureAwait(false);
    }

    private static void ApplyToken(PipelineMessage message, string token) =>
        message.Request?.Headers.Set("Authorization", $"Bearer {token}");

    private string GetTokenSync()
    {
        if (TryGetCached(out var cached))
        {
            return cached;
        }

        var fresh = _credential.GetToken(new TokenRequestContext(_scopes), CancellationToken.None);
        return Store(fresh);
    }

    private async ValueTask<string> GetTokenAsync()
    {
        if (TryGetCached(out var cached))
        {
            return cached;
        }

        var fresh = await _credential
            .GetTokenAsync(new TokenRequestContext(_scopes), CancellationToken.None)
            .ConfigureAwait(false);
        return Store(fresh);
    }

    private bool TryGetCached(out string token)
    {
        lock (_gate)
        {
            if (_cached.Token is not null && _cached.ExpiresOn > DateTimeOffset.UtcNow.Add(RefreshWindow))
            {
                token = _cached.Token;
                return true;
            }
        }

        token = string.Empty;
        return false;
    }

    private string Store(AccessToken fresh)
    {
        lock (_gate)
        {
            _cached = fresh;
        }

        return fresh.Token;
    }
}
