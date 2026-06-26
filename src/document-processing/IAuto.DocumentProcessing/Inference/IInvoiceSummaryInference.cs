namespace IAuto.DocumentProcessing.Inference;

public interface IInvoiceSummaryInference
{
    Task<string> CompleteAsync(string systemPrompt, string userPrompt, CancellationToken cancellationToken);
}
