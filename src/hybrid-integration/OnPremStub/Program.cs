using IAuto.HybridIntegration.OnPremStub;

var builder = WebApplication.CreateBuilder(args);

// The on-prem system is represented by a single in-memory repository. The explicit factory
// pins the seeded parameterless constructor: without it the DI container would greedily pick
// the longest constructor — OrderRepository(IEnumerable<OrderStatus>) — and inject an empty
// sequence, leaving the host with no demo data.
builder.Services.AddSingleton(_ => new OrderRepository());

var app = builder.Build();

// Liveness probe — Logic Apps / APIM health checks and the lab validation script call this.
app.MapGet("/health", () => Results.Ok(new HealthResponse("healthy")))
    .WithName("Health");

// List every order. Handy for demos and for discovering the seeded ids.
app.MapGet("/orders", (OrderRepository repository) => Results.Ok(repository.GetAll()))
    .WithName("ListOrders");

// Resolve a single order, returning 404 when the id is unknown.
app.MapGet("/orders/{orderId}", (string orderId, OrderRepository repository) =>
        repository.TryGet(orderId, out var order) && order is not null
            ? Results.Ok(order)
            : Results.NotFound(new ProblemResponse($"Order '{orderId}' was not found.")))
    .WithName("GetOrder");

app.Run();

/// <summary>Liveness payload returned by the <c>/health</c> endpoint.</summary>
/// <param name="Status">Always <c>healthy</c> when the host is serving requests.</param>
internal sealed record HealthResponse(string Status);

/// <summary>Minimal error payload returned for not-found responses.</summary>
/// <param name="Message">Human-readable description of the problem.</param>
internal sealed record ProblemResponse(string Message);

namespace IAuto.HybridIntegration.OnPremStub
{
    /// <summary>Entry-point marker so <c>WebApplicationFactory</c>-based integration tests can host the API.</summary>
    public sealed partial class OnPremStubApi;
}
