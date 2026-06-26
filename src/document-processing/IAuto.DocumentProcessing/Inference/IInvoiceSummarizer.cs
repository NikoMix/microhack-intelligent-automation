using IAuto.DocumentProcessing.Models;

namespace IAuto.DocumentProcessing.Inference;

public interface IInvoiceSummarizer
{
    Task<InvoiceSummaryResult> SummarizeAsync(InvoiceAnalysis invoice, CancellationToken cancellationToken);
}
