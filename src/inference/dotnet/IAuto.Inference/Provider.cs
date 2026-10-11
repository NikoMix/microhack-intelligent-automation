namespace IAuto.Inference;

/// <summary>Supported inference providers. Mirrors the Python <c>Provider</c> enum.</summary>
public enum Provider
{
    /// <summary>GitHub Models — free default, OpenAI-compatible.</summary>
    GitHub,

    /// <summary>Azure OpenAI (API key or Entra ID).</summary>
    AzureOpenAI,

    /// <summary>Azure AI Foundry via its OpenAI-compatible endpoint.</summary>
    Foundry,
}
