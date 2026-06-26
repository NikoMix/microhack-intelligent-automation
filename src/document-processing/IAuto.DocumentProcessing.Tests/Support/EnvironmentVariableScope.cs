namespace IAuto.DocumentProcessing.Tests;

/// <summary>
/// Temporarily sets process environment variables for the lifetime of the scope and restores
/// their previous values on disposal. Used to exercise configuration-driven composition without
/// contacting any inference provider or Azure service.
/// </summary>
internal sealed class EnvironmentVariableScope : IDisposable
{
    private readonly Dictionary<string, string?> _previousValues = new(StringComparer.Ordinal);

    private EnvironmentVariableScope()
    {
    }

    /// <summary>Set the supplied environment variables, capturing their prior values.</summary>
    /// <param name="values">The environment variables to set for the scope.</param>
    /// <returns>A disposable scope that restores the prior values when disposed.</returns>
    public static EnvironmentVariableScope Set(IReadOnlyDictionary<string, string?> values)
    {
        ArgumentNullException.ThrowIfNull(values);

        var scope = new EnvironmentVariableScope();
        foreach (KeyValuePair<string, string?> pair in values)
        {
            scope._previousValues[pair.Key] = Environment.GetEnvironmentVariable(pair.Key);
            Environment.SetEnvironmentVariable(pair.Key, pair.Value);
        }

        return scope;
    }

    /// <summary>Restore every environment variable captured by this scope.</summary>
    public void Dispose()
    {
        foreach (KeyValuePair<string, string?> pair in _previousValues)
        {
            Environment.SetEnvironmentVariable(pair.Key, pair.Value);
        }
    }
}
