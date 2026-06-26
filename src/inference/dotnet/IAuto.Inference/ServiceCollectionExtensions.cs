using Microsoft.Extensions.AI;
using Microsoft.Extensions.DependencyInjection;

namespace IAuto.Inference;

/// <summary>Dependency-injection helpers for registering the modular inference client.</summary>
public static class ServiceCollectionExtensions
{
    /// <summary>
    /// Register a singleton <see cref="IChatClient"/> resolved from the supplied options,
    /// or from environment variables when none are provided.
    /// </summary>
    public static IServiceCollection AddModularInference(
        this IServiceCollection services,
        InferenceOptions? options = null)
    {
        ArgumentNullException.ThrowIfNull(services);
        var resolved = options ?? InferenceOptions.FromEnvironment();
        services.AddSingleton(resolved);
        services.AddSingleton(ChatClientFactory.Create(resolved));
        return services;
    }

    /// <summary>
    /// Register a singleton <see cref="IChatClient"/> using an options delegate, starting
    /// from the environment-derived defaults.
    /// </summary>
    public static IServiceCollection AddModularInference(
        this IServiceCollection services,
        Action<InferenceOptions> configure)
    {
        ArgumentNullException.ThrowIfNull(services);
        ArgumentNullException.ThrowIfNull(configure);

        var options = InferenceOptions.FromEnvironment();
        configure(options);
        return services.AddModularInference(options);
    }
}
