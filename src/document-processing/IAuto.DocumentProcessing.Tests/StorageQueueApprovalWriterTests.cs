using System.Text.Json;
using IAuto.DocumentProcessing.HumanInTheLoop;
using IAuto.DocumentProcessing.Models;

namespace IAuto.DocumentProcessing.Tests;

/// <summary>Tests the approval envelope creation and JSON contract consumed by a reviewer experience.</summary>
public sealed class StorageQueueApprovalWriterTests
{
    private static readonly JsonSerializerOptions WebOptions = new(JsonSerializerDefaults.Web);

    private static ApprovalRequest Request() =>
        new()
        {
            DocumentName = "invoice.pdf",
            ModelId = "prebuilt-invoice",
            OverallConfidence = 0.42,
            Reasons = ["Low confidence"],
            Fields = [new ExtractedField("InvoiceTotal", "100", 0.42, "Currency")],
        };

    [Fact]
    public void CreateEnvelope_PopulatesIdentityAndRequest()
    {
        var createdAt = new DateTimeOffset(2026, 1, 1, 12, 0, 0, TimeSpan.Zero);

        ApprovalEnvelope envelope = StorageQueueApprovalWriter.CreateEnvelope(Request(), createdAt);

        Assert.False(string.IsNullOrWhiteSpace(envelope.Id));
        Assert.Equal(createdAt, envelope.CreatedAt);
        Assert.Equal("invoice.pdf", envelope.Request.DocumentName);
        Assert.Equal("1.0", envelope.SchemaVersion);
    }

    [Fact]
    public void Serialize_RoundTripsThroughWebJson()
    {
        ApprovalEnvelope envelope = StorageQueueApprovalWriter.CreateEnvelope(Request(), DateTimeOffset.UtcNow);

        string json = StorageQueueApprovalWriter.Serialize(envelope);
        ApprovalEnvelope? roundTrip = JsonSerializer.Deserialize<ApprovalEnvelope>(json, WebOptions);

        Assert.NotNull(roundTrip);
        Assert.Equal(envelope.Id, roundTrip!.Id);
        Assert.Equal(envelope.Request.DocumentName, roundTrip.Request.DocumentName);
        Assert.Single(roundTrip.Request.Fields);
        Assert.Equal("InvoiceTotal", roundTrip.Request.Fields[0].Name);
    }
}
