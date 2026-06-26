using System.ClientModel;
using System.ClientModel.Primitives;
using Azure.AI.OpenAI;
using Azure.Identity;
using Microsoft.Extensions.AI;
using OpenAI;

namespace IAuto.Inference;

/// <summary>
/// Builds a provider-agnostic <see cref="IChatClient"/> from <see cref="InferenceOptions"/>.
/// All three providers are unified on the OpenAI SDK and surfaced through the
/// <c>Microsoft.Extensions.AI</c> abstraction so downstream code (agents, RAG, tools)
/// never depends on a specific backend.
/// </summary>
public static class ChatClientFactory
{
    /// <summary>
    /// Create an <see cref="IChatClient"/> for the configured provider. Validates the
    /// options first and throws <see cref="InferenceConfigurationException"/> when the
    /// minimum configuration is missing.
    /// </summary>
    public static IChatClient Create(InferenceOptions options)
    {
        ArgumentNullException.ThrowIfNull(options);
        options.Validate();

        return options.Provider switch
        {
            Provider.GitHub => CreateGitHub(options),
            Provider.AzureOpenAI => CreateAzureOpenAI(options),
            Provider.Foundry => CreateFoundry(options),
            _ => throw new InferenceConfigurationException($"Unknown provider '{options.Provider}'."),
        };
    }

    /// <summary>Convenience overload that reads configuration from the environment.</summary>
    public static IChatClient CreateFromEnvironment() => Create(InferenceOptions.FromEnvironment());

    private static IChatClient CreateGitHub(InferenceOptions options)
    {
        var clientOptions = new OpenAIClientOptions { Endpoint = new Uri(options.GitHubModelsEndpoint) };
        var client = new OpenAIClient(new ApiKeyCredential(options.GitHubToken!), clientOptions);
        return client.GetChatClient(options.GitHubModelsModel).AsIChatClient();
    }

    private static IChatClient CreateAzureOpenAI(InferenceOptions options)
    {
        var endpoint = new Uri(options.AzureOpenAIEndpoint!);
        var deployment = options.AzureOpenAIDeployment!;

        var client = string.IsNullOrWhiteSpace(options.AzureOpenAIApiKey)
            ? new AzureOpenAIClient(endpoint, new DefaultAzureCredential())
            : new AzureOpenAIClient(endpoint, new ApiKeyCredential(options.AzureOpenAIApiKey));

        return client.GetChatClient(deployment).AsIChatClient();
    }

    private static IChatClient CreateFoundry(InferenceOptions options)
    {
        var clientOptions = new OpenAIClientOptions { Endpoint = new Uri(options.FoundryEndpoint!) };

        ApiKeyCredential credential;
        if (string.IsNullOrWhiteSpace(options.FoundryApiKey))
        {
            // Keyless: the policy overwrites the Authorization header with an Entra token.
            credential = new ApiKeyCredential("entra-id-placeholder");
            clientOptions.AddPolicy(
                new EntraBearerPolicy(new DefaultAzureCredential(), InferenceOptions.CognitiveServicesScope),
                PipelinePosition.PerTry);
        }
        else
        {
            credential = new ApiKeyCredential(options.FoundryApiKey);
        }

        var client = new OpenAIClient(credential, clientOptions);
        return client.GetChatClient(options.FoundryModel!).AsIChatClient();
    }
}
