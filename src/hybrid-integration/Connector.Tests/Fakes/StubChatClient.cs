using System.Runtime.CompilerServices;
using Microsoft.Extensions.AI;

namespace IAuto.HybridIntegration.Connector.Tests.Fakes;

/// <summary>
/// In-memory <see cref="IChatClient"/> that records the messages it receives and returns a
/// configurable reply. Lets the enricher be tested without any inference provider.
/// </summary>
internal sealed class StubChatClient : IChatClient
{
    public string Reply { get; set; } = "stubbed-response";

    public IList<ChatMessage>? LastMessages { get; private set; }

    public int CallCount { get; private set; }

    public Task<ChatResponse> GetResponseAsync(
        IEnumerable<ChatMessage> messages,
        ChatOptions? options = null,
        CancellationToken cancellationToken = default)
    {
        LastMessages = messages.ToList();
        CallCount++;
        return Task.FromResult(new ChatResponse(new ChatMessage(ChatRole.Assistant, Reply)));
    }

    public async IAsyncEnumerable<ChatResponseUpdate> GetStreamingResponseAsync(
        IEnumerable<ChatMessage> messages,
        ChatOptions? options = null,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        LastMessages = messages.ToList();
        CallCount++;
        yield return new ChatResponseUpdate(ChatRole.Assistant, Reply);
        await Task.CompletedTask.ConfigureAwait(false);
    }

    public object? GetService(Type serviceType, object? serviceKey = null) => null;

    public void Dispose()
    {
    }
}
