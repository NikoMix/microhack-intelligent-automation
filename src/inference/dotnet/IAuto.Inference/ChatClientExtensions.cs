using Microsoft.Extensions.AI;

namespace IAuto.Inference;

/// <summary>Ergonomic helpers used throughout the labs on top of <see cref="IChatClient"/>.</summary>
public static class ChatClientExtensions
{
    /// <summary>
    /// Send a single user prompt and return the assistant's text response. A thin wrapper
    /// over <see cref="ChatClientExtensions"/> in Microsoft.Extensions.AI to keep lab code
    /// terse and provider-agnostic.
    /// </summary>
    public static async Task<string> CompleteTextAsync(
        this IChatClient client,
        string prompt,
        string? systemPrompt = null,
        CancellationToken cancellationToken = default)
    {
        ArgumentNullException.ThrowIfNull(client);
        ArgumentException.ThrowIfNullOrWhiteSpace(prompt);

        var messages = new List<ChatMessage>(2);
        if (!string.IsNullOrWhiteSpace(systemPrompt))
        {
            messages.Add(new ChatMessage(ChatRole.System, systemPrompt));
        }

        messages.Add(new ChatMessage(ChatRole.User, prompt));

        var response = await client.GetResponseAsync(messages, options: null, cancellationToken)
            .ConfigureAwait(false);
        return response.Text;
    }
}
