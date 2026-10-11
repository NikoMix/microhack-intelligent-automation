namespace IAuto.Inference;

/// <summary>
/// Thrown when provider configuration is missing or inconsistent. The message is
/// actionable so learners can self-correct during the labs.
/// </summary>
public sealed class InferenceConfigurationException : Exception
{
    /// <summary>Create the exception with an actionable message.</summary>
    public InferenceConfigurationException(string message) : base(message)
    {
    }

    /// <summary>Create the exception with a message and inner cause.</summary>
    public InferenceConfigurationException(string message, Exception innerException)
        : base(message, innerException)
    {
    }
}
