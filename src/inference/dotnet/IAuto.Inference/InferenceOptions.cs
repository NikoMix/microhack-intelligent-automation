using System.Globalization;

namespace IAuto.Inference;

/// <summary>
/// Strongly-typed inference configuration mirroring the shared environment-variable
/// contract used by the Python <c>iauto-inference</c> package. Keep both in sync.
/// </summary>
public sealed class InferenceOptions
{
    /// <summary>Entra ID token scope for Azure AI services.</summary>
    public const string CognitiveServicesScope = "https://cognitiveservices.azure.com/.default";

    /// <summary>Selected provider. Defaults to <see cref="Provider.GitHub"/>.</summary>
    public Provider Provider { get; set; } = Provider.GitHub;

    // --- GitHub Models ---

    /// <summary>GitHub token (<c>GITHUB_TOKEN</c>) used as the API key for GitHub Models.</summary>
    public string? GitHubToken { get; set; }

    /// <summary>GitHub Models endpoint. Defaults to the public inference URL.</summary>
    public string GitHubModelsEndpoint { get; set; } = "https://models.github.ai/inference";

    /// <summary>GitHub Models model id. Defaults to <c>openai/gpt-4o-mini</c>.</summary>
    public string GitHubModelsModel { get; set; } = "openai/gpt-4o-mini";

    // --- Azure OpenAI ---

    /// <summary>Azure OpenAI resource endpoint, e.g. <c>https://my-aoai.openai.azure.com</c>.</summary>
    public string? AzureOpenAIEndpoint { get; set; }

    /// <summary>Azure OpenAI API key. When empty, Entra ID (DefaultAzureCredential) is used.</summary>
    public string? AzureOpenAIApiKey { get; set; }

    /// <summary>Azure OpenAI deployment name (your chat model deployment).</summary>
    public string? AzureOpenAIDeployment { get; set; }

    // --- Azure AI Foundry ---

    /// <summary>Azure AI Foundry OpenAI-compatible endpoint.</summary>
    public string? FoundryEndpoint { get; set; }

    /// <summary>Azure AI Foundry model/deployment id.</summary>
    public string? FoundryModel { get; set; }

    /// <summary>Azure AI Foundry API key. When empty, Entra ID is used.</summary>
    public string? FoundryApiKey { get; set; }

    // --- Shared tunables ---

    /// <summary>Per-request timeout in seconds. Defaults to 60.</summary>
    public int TimeoutSeconds { get; set; } = 60;

    /// <summary>Max client retry attempts. Defaults to 3.</summary>
    public int MaxRetries { get; set; } = 3;

    /// <summary>
    /// Build options from environment variables using the shared contract. Unset values
    /// fall back to the defaults above.
    /// </summary>
    public static InferenceOptions FromEnvironment(IDictionary<string, string?>? source = null)
    {
        string? Get(string key) =>
            source is not null
                ? (source.TryGetValue(key, out var v) ? v : null)
                : Environment.GetEnvironmentVariable(key);

        var options = new InferenceOptions
        {
            Provider = ParseProvider(Get("INFERENCE_PROVIDER")),
            GitHubToken = Get("GITHUB_TOKEN"),
            AzureOpenAIEndpoint = Get("AZURE_OPENAI_ENDPOINT"),
            AzureOpenAIApiKey = Get("AZURE_OPENAI_API_KEY"),
            AzureOpenAIDeployment = Get("AZURE_OPENAI_DEPLOYMENT"),
            FoundryEndpoint = Get("AZURE_AI_FOUNDRY_ENDPOINT"),
            FoundryModel = Get("AZURE_AI_FOUNDRY_MODEL"),
            FoundryApiKey = Get("AZURE_AI_FOUNDRY_API_KEY"),
        };

        var ghEndpoint = Get("GITHUB_MODELS_ENDPOINT");
        if (!string.IsNullOrWhiteSpace(ghEndpoint))
        {
            options.GitHubModelsEndpoint = ghEndpoint;
        }

        var ghModel = Get("GITHUB_MODELS_MODEL");
        if (!string.IsNullOrWhiteSpace(ghModel))
        {
            options.GitHubModelsModel = ghModel;
        }

        options.TimeoutSeconds = ParseInt(Get("INFERENCE_TIMEOUT"), options.TimeoutSeconds);
        options.MaxRetries = ParseInt(Get("INFERENCE_MAX_RETRIES"), options.MaxRetries);
        return options;
    }

    /// <summary>Resolve the model/deployment id appropriate for the selected provider.</summary>
    public string DefaultModel() => Provider switch
    {
        Provider.GitHub => GitHubModelsModel,
        Provider.AzureOpenAI => AzureOpenAIDeployment
            ?? throw new InferenceConfigurationException(
                "AZURE_OPENAI_DEPLOYMENT is required for the azure_openai provider."),
        Provider.Foundry => FoundryModel
            ?? throw new InferenceConfigurationException(
                "AZURE_AI_FOUNDRY_MODEL is required for the foundry provider."),
        _ => throw new InferenceConfigurationException($"Unknown provider '{Provider}'."),
    };

    /// <summary>
    /// Validate that the minimum configuration for the selected provider is present.
    /// Throws <see cref="InferenceConfigurationException"/> with an actionable message.
    /// </summary>
    public void Validate()
    {
        switch (Provider)
        {
            case Provider.GitHub:
                Require(GitHubToken, "GITHUB_TOKEN", "GitHub Models");
                break;
            case Provider.AzureOpenAI:
                Require(AzureOpenAIEndpoint, "AZURE_OPENAI_ENDPOINT", "Azure OpenAI");
                Require(AzureOpenAIDeployment, "AZURE_OPENAI_DEPLOYMENT", "Azure OpenAI");
                break;
            case Provider.Foundry:
                Require(FoundryEndpoint, "AZURE_AI_FOUNDRY_ENDPOINT", "Azure AI Foundry");
                Require(FoundryModel, "AZURE_AI_FOUNDRY_MODEL", "Azure AI Foundry");
                break;
            default:
                throw new InferenceConfigurationException($"Unknown provider '{Provider}'.");
        }
    }

    private static void Require(string? value, string envVar, string providerLabel)
    {
        if (string.IsNullOrWhiteSpace(value))
        {
            throw new InferenceConfigurationException(
                $"{envVar} is required for the {providerLabel} provider. " +
                "Set it in your environment or .env file.");
        }
    }

    private static Provider ParseProvider(string? raw)
    {
        if (string.IsNullOrWhiteSpace(raw))
        {
            return Provider.GitHub;
        }

        return raw.Trim().ToLowerInvariant() switch
        {
            "github" or "github_models" or "githubmodels" => Provider.GitHub,
            "azure_openai" or "azureopenai" or "aoai" => Provider.AzureOpenAI,
            "foundry" or "azure_ai_foundry" or "azureaifoundry" => Provider.Foundry,
            _ => throw new InferenceConfigurationException(
                $"Unknown INFERENCE_PROVIDER '{raw}'. Use github, azure_openai, or foundry."),
        };
    }

    private static int ParseInt(string? raw, int fallback) =>
        int.TryParse(raw, NumberStyles.Integer, CultureInfo.InvariantCulture, out var parsed)
            ? parsed
            : fallback;
}
