using IAuto.DocumentProcessing.Models;

namespace IAuto.DocumentProcessing.DocumentIntelligence;

public interface IInvoiceFieldMapper
{
    InvoiceAnalysis Map(RawInvoiceDocument document);
}
