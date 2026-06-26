using IAuto.DocumentProcessing.Inference;

namespace IAuto.DocumentProcessing.Tests.Fakes;

internal sealed class StubInvoiceSummaryInference : IInvoiceSummaryInference
{
    private readonly string _response;

    public StubInvoiceSummaryInference(string response)
    {
        _response = response;
    }

    public string? LastSystemPrompt { get; private set; }

    public string? LastUserPrompt { get; private set; }

    public Task<string> CompleteAsync(string systemPrompt, string userPrompt, CancellationToken cancellationToken)
    {
        LastSystemPrompt = systemPrompt;
        LastUserPrompt = userPrompt;
        return Task.FromResult(_response);
    }
}
