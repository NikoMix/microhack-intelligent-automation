using System.Runtime.CompilerServices;
using Microsoft.Extensions.AI;

namespace IAuto.DocumentProcessing.Tests.Fakes;

/// <summary>
/// Minimal in-memory <see cref="IChatClient"/> used to exercise modular-inference post-processing
/// without any network or provider dependency.
/// </summary>
internal sealed class StubChatClient : IChatClient
{
    public string Reply { get; set; } = "stubbed-response";

    public bool ThrowOnCall { get; set; }

    public IList<ChatMessage>? LastMessages { get; private set; }

    public Task<ChatResponse> GetResponseAsync(
        IEnumerable<ChatMessage> messages,
        ChatOptions? options = null,
        CancellationToken cancellationToken = default)
    {
        if (ThrowOnCall)
        {
            throw new InvalidOperationException("Stub chat client failure.");
        }

        LastMessages = messages.ToList();
        return Task.FromResult(new ChatResponse(new ChatMessage(ChatRole.Assistant, Reply)));
    }

    public async IAsyncEnumerable<ChatResponseUpdate> GetStreamingResponseAsync(
        IEnumerable<ChatMessage> messages,
        ChatOptions? options = null,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        LastMessages = messages.ToList();
        yield return new ChatResponseUpdate(ChatRole.Assistant, Reply);
        await Task.CompletedTask.ConfigureAwait(false);
    }

    public object? GetService(Type serviceType, object? serviceKey = null) => null;

    public void Dispose()
    {
    }
}
