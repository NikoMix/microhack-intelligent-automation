using IAuto.Inference;
using Microsoft.Extensions.AI;

namespace IAuto.DocumentProcessing.Inference;

public sealed class ModularInferenceSummaryClient : IInvoiceSummaryInference
{
    private readonly IChatClient _chatClient;

    public ModularInferenceSummaryClient(IChatClient chatClient)
    {
        _chatClient = chatClient ?? throw new ArgumentNullException(nameof(chatClient));
    }

    public Task<string> CompleteAsync(string systemPrompt, string userPrompt, CancellationToken cancellationToken) =>
        _chatClient.CompleteTextAsync(userPrompt, systemPrompt, cancellationToken);
}
