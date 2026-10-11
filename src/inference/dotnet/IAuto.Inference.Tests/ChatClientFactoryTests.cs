using IAuto.Inference;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.DependencyInjection;

namespace IAuto.Inference.Tests;

public sealed class ChatClientFactoryTests
{
    [Fact]
    public void Create_NullOptions_Throws() =>
        Assert.Throws<ArgumentNullException>(() => ChatClientFactory.Create(null!));

    [Fact]
    public void Create_GitHubMissingToken_ThrowsConfiguration()
    {
        var options = new InferenceOptions { Provider = Provider.GitHub };

        Assert.Throws<InferenceConfigurationException>(() => ChatClientFactory.Create(options));
    }

    [Fact]
    public void Create_GitHubWithToken_ReturnsClient()
    {
        var options = new InferenceOptions { Provider = Provider.GitHub, GitHubToken = "ghp_fake" };

        using var client = ChatClientFactory.Create(options);

        Assert.NotNull(client);
    }

    [Fact]
    public void Create_AzureOpenAIKeyless_ReturnsClient()
    {
        var options = new InferenceOptions
        {
            Provider = Provider.AzureOpenAI,
            AzureOpenAIEndpoint = "https://contoso.openai.azure.com",
            AzureOpenAIDeployment = "gpt-4o",
        };

        using var client = ChatClientFactory.Create(options);

        Assert.NotNull(client);
    }

    [Fact]
    public void Create_FoundryKeylessAddsPolicy_ReturnsClient()
    {
        var options = new InferenceOptions
        {
            Provider = Provider.Foundry,
            FoundryEndpoint = "https://contoso.services.ai.azure.com",
            FoundryModel = "phi-4",
        };

        using var client = ChatClientFactory.Create(options);

        Assert.NotNull(client);
    }
}

public sealed class ServiceCollectionExtensionsTests
{
    [Fact]
    public void AddModularInference_RegistersChatClientAndOptions()
    {
        var services = new ServiceCollection();
        services.AddModularInference(new InferenceOptions
        {
            Provider = Provider.GitHub,
            GitHubToken = "ghp_fake",
        });

        using var provider = services.BuildServiceProvider();

        Assert.NotNull(provider.GetRequiredService<IChatClient>());
        Assert.Equal(Provider.GitHub, provider.GetRequiredService<InferenceOptions>().Provider);
    }

    [Fact]
    public void AddModularInference_ConfigureDelegate_Applies()
    {
        var services = new ServiceCollection();
        services.AddModularInference(options =>
        {
            options.Provider = Provider.GitHub;
            options.GitHubToken = "ghp_fake";
            options.GitHubModelsModel = "openai/gpt-4o";
        });

        using var provider = services.BuildServiceProvider();

        Assert.Equal("openai/gpt-4o", provider.GetRequiredService<InferenceOptions>().GitHubModelsModel);
    }
}
