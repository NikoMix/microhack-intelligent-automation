using IAuto.DocumentProcessing.Models;

namespace IAuto.DocumentProcessing.Storage;

public interface IProcessedInvoiceWriter
{
    Task WriteAsync(ProcessedInvoiceResult result, CancellationToken cancellationToken);
}
