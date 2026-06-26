namespace IAuto.HybridIntegration.Connector.Tests.Fakes;

/// <summary>
/// Test double for <see cref="HttpMessageHandler"/> that returns a caller-supplied response and
/// captures the last request, so the typed <c>OnPremClient</c> can be tested without a server.
/// </summary>
internal sealed class StubHttpMessageHandler : HttpMessageHandler
{
    private readonly Func<HttpRequestMessage, HttpResponseMessage> _responder;

    public StubHttpMessageHandler(Func<HttpRequestMessage, HttpResponseMessage> responder) =>
        _responder = responder;

    public HttpRequestMessage? LastRequest { get; private set; }

    protected override Task<HttpResponseMessage> SendAsync(
        HttpRequestMessage request,
        CancellationToken cancellationToken)
    {
        LastRequest = request;
        return Task.FromResult(_responder(request));
    }
}
