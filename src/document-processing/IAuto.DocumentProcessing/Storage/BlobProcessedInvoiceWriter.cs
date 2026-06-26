using System.Text.Json;
using Azure.Storage.Blobs;
using Azure.Storage.Blobs.Models;
using IAuto.DocumentProcessing.Configuration;
using IAuto.DocumentProcessing.Models;
using Microsoft.Extensions.Options;

namespace IAuto.DocumentProcessing.Storage;

public sealed class BlobProcessedInvoiceWriter : IProcessedInvoiceWriter
{
    private static readonly JsonSerializerOptions JsonOptions = new(JsonSerializerDefaults.Web) { WriteIndented = true };
    private readonly BlobContainerClient _container;

    public BlobProcessedInvoiceWriter(BlobServiceClient blobServiceClient, IOptions<DocumentProcessingOptions> options)
    {
        ArgumentNullException.ThrowIfNull(blobServiceClient);
        ArgumentNullException.ThrowIfNull(options);
        _container = blobServiceClient.GetBlobContainerClient(options.Value.ProcessedContainer);
    }

    public async Task WriteAsync(ProcessedInvoiceResult result, CancellationToken cancellationToken)
    {
        ArgumentNullException.ThrowIfNull(result);

        await _container.CreateIfNotExistsAsync(PublicAccessType.None, cancellationToken: cancellationToken).ConfigureAwait(false);
        var blob = _container.GetBlobClient(result.ProcessedBlobName);
        await using var content = new MemoryStream(JsonSerializer.SerializeToUtf8Bytes(result, JsonOptions));
        await blob.UploadAsync(
            content,
            new BlobUploadOptions
            {
                HttpHeaders = new BlobHttpHeaders { ContentType = "application/json" },
                Metadata = new Dictionary<string, string>
                {
                    ["sourceBlobName"] = result.SourceBlobName,
                    ["invocationId"] = result.Telemetry.InvocationId,
                },
            },
            cancellationToken).ConfigureAwait(false);
    }
}
