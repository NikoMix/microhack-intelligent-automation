using IAuto.Inference;

namespace IAuto.Inference.Tests;

public sealed class InferenceOptionsTests
{
    [Fact]
    public void FromEnvironment_DefaultsToGitHub()
    {
        var options = InferenceOptions.FromEnvironment(new Dictionary<string, string?>());

        Assert.Equal(Provider.GitHub, options.Provider);
        Assert.Equal("https://models.github.ai/inference", options.GitHubModelsEndpoint);
        Assert.Equal("openai/gpt-4o-mini", options.GitHubModelsModel);
        Assert.Equal(60, options.TimeoutSeconds);
        Assert.Equal(3, options.MaxRetries);
    }

    [Theory]
    [InlineData("github", Provider.GitHub)]
    [InlineData("GitHub", Provider.GitHub)]
    [InlineData("azure_openai", Provider.AzureOpenAI)]
    [InlineData("aoai", Provider.AzureOpenAI)]
    [InlineData("foundry", Provider.Foundry)]
    [InlineData("azure_ai_foundry", Provider.Foundry)]
    public void FromEnvironment_ParsesProviderAliases(string raw, Provider expected)
    {
        var options = InferenceOptions.FromEnvironment(
            new Dictionary<string, string?> { ["INFERENCE_PROVIDER"] = raw });

        Assert.Equal(expected, options.Provider);
    }

    [Fact]
    public void FromEnvironment_UnknownProvider_Throws()
    {
        Assert.Throws<InferenceConfigurationException>(() =>
            InferenceOptions.FromEnvironment(
                new Dictionary<string, string?> { ["INFERENCE_PROVIDER"] = "bedrock" }));
    }

    [Fact]
    public void FromEnvironment_ReadsAzureAndTunables()
    {
        var options = InferenceOptions.FromEnvironment(new Dictionary<string, string?>
        {
            ["INFERENCE_PROVIDER"] = "azure_openai",
            ["AZURE_OPENAI_ENDPOINT"] = "https://contoso.openai.azure.com",
            ["AZURE_OPENAI_DEPLOYMENT"] = "gpt-4o",
            ["AZURE_OPENAI_API_KEY"] = "secret",
            ["INFERENCE_TIMEOUT"] = "120",
            ["INFERENCE_MAX_RETRIES"] = "5",
        });

        Assert.Equal(Provider.AzureOpenAI, options.Provider);
        Assert.Equal("https://contoso.openai.azure.com", options.AzureOpenAIEndpoint);
        Assert.Equal("gpt-4o", options.AzureOpenAIDeployment);
        Assert.Equal("secret", options.AzureOpenAIApiKey);
        Assert.Equal(120, options.TimeoutSeconds);
        Assert.Equal(5, options.MaxRetries);
        Assert.Equal("gpt-4o", options.DefaultModel());
    }

    [Fact]
    public void FromEnvironment_InvalidIntsFallBackToDefaults()
    {
        var options = InferenceOptions.FromEnvironment(new Dictionary<string, string?>
        {
            ["INFERENCE_TIMEOUT"] = "not-a-number",
            ["INFERENCE_MAX_RETRIES"] = "",
        });

        Assert.Equal(60, options.TimeoutSeconds);
        Assert.Equal(3, options.MaxRetries);
    }

    [Fact]
    public void Validate_GitHubWithoutToken_Throws()
    {
        var options = new InferenceOptions { Provider = Provider.GitHub, GitHubToken = null };

        var ex = Assert.Throws<InferenceConfigurationException>(options.Validate);
        Assert.Contains("GITHUB_TOKEN", ex.Message, StringComparison.Ordinal);
    }

    [Fact]
    public void Validate_AzureOpenAIMissingDeployment_Throws()
    {
        var options = new InferenceOptions
        {
            Provider = Provider.AzureOpenAI,
            AzureOpenAIEndpoint = "https://contoso.openai.azure.com",
        };

        var ex = Assert.Throws<InferenceConfigurationException>(options.Validate);
        Assert.Contains("AZURE_OPENAI_DEPLOYMENT", ex.Message, StringComparison.Ordinal);
    }

    [Fact]
    public void Validate_FoundryMissingEndpoint_Throws()
    {
        var options = new InferenceOptions { Provider = Provider.Foundry, FoundryModel = "phi-4" };

        var ex = Assert.Throws<InferenceConfigurationException>(options.Validate);
        Assert.Contains("AZURE_AI_FOUNDRY_ENDPOINT", ex.Message, StringComparison.Ordinal);
    }
}
