using IAuto.DocumentProcessing.Models;

namespace IAuto.DocumentProcessing.DocumentIntelligence;

public interface IDocumentInvoiceAnalyzer
{
    Task<InvoiceAnalysis> AnalyzeInvoiceAsync(Stream document, string sourceBlobName, CancellationToken cancellationToken);
}
