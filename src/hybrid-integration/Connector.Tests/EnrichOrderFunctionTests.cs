using System.Text;
using IAuto.HybridIntegration.Connector.Functions;
using IAuto.HybridIntegration.Connector.Models;
using IAuto.HybridIntegration.Connector.Tests.Fakes;
using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.Mvc;
using Microsoft.Extensions.Logging.Abstractions;

namespace IAuto.HybridIntegration.Connector.Tests;

/// <summary>Unit tests for <see cref="EnrichOrderFunction"/> request handling.</summary>
public sealed class EnrichOrderFunctionTests
{
    private static HttpRequest BuildRequest(string? body, string contentType = "application/json")
    {
        var context = new DefaultHttpContext();
        if (body is not null)
        {
            var bytes = Encoding.UTF8.GetBytes(body);
            context.Request.Body = new MemoryStream(bytes);
            context.Request.ContentLength = bytes.Length;
        }

        context.Request.ContentType = contentType;
        return context.Request;
    }

    private static EnrichOrderFunction CreateFunction(StubOrderEnricher enricher) =>
        new(enricher, NullLogger<EnrichOrderFunction>.Instance);

    [Fact]
    public async Task RunAsync_WithValidBody_Returns200WithResult()
    {
        var enricher = new StubOrderEnricher();
        var function = CreateFunction(enricher);
        var request = BuildRequest("""{"orderId":"ORD-1001","question":"Where is my order?"}""");

        var result = await function.RunAsync(request, CancellationToken.None);

        var ok = Assert.IsType<OkObjectResult>(result);
        var payload = Assert.IsType<EnrichmentResult>(ok.Value);
        Assert.Equal("ORD-1001", payload.OrderId);
        Assert.Equal("ORD-1001", enricher.LastRequest!.OrderId);
        Assert.Equal("Where is my order?", enricher.LastRequest.Question);
    }

    [Fact]
    public async Task RunAsync_WithMissingFields_Returns400()
    {
        var function = CreateFunction(new StubOrderEnricher());
        var request = BuildRequest("""{"orderId":"","question":""}""");

        var result = await function.RunAsync(request, CancellationToken.None);

        Assert.IsType<BadRequestObjectResult>(result);
    }

    [Fact]
    public async Task RunAsync_WithMalformedJson_Returns400()
    {
        var function = CreateFunction(new StubOrderEnricher());
        var request = BuildRequest("{ this is not json");

        var result = await function.RunAsync(request, CancellationToken.None);

        Assert.IsType<BadRequestObjectResult>(result);
    }

    [Fact]
    public async Task RunAsync_WithEmptyBody_Returns400()
    {
        var function = CreateFunction(new StubOrderEnricher());
        var request = BuildRequest(string.Empty);

        var result = await function.RunAsync(request, CancellationToken.None);

        Assert.IsType<BadRequestObjectResult>(result);
    }
}
