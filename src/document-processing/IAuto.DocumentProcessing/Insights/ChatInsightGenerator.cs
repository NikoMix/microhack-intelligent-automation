using System.Text.Json;
using IAuto.DocumentProcessing.Abstractions;
using IAuto.DocumentProcessing.Models;
using IAuto.DocumentProcessing.Pipeline;
using IAuto.Inference;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Options;

namespace IAuto.DocumentProcessing.Insights;

/// <summary>
/// Generates document insights (summary and classification) by calling the shared modular
/// inference <see cref="IChatClient"/>. Provider selection (GitHub Models, Azure OpenAI,
/// or Azure AI Foundry) is configuration-driven via the inference layer and never hard-coded.
/// Failures are swallowed so insights remain a best-effort enrichment.
/// </summary>
public sealed class ChatInsightGenerator : IDocumentInsightGenerator
{
    private const int MaxContentChars = 4000;
    private static readonly string[] DefaultCategories =
        ["Invoice", "Receipt", "Contract", "Statement", "Other"];

    private readonly IChatClient _chatClient;
    private readonly DocumentProcessingOptions _options;
    private readonly ILogger<ChatInsightGenerator> _logger;

    /// <summary>Create the generator from a chat client and pipeline options.</summary>
    /// <param name="chatClient">Modular inference chat client.</param>
    /// <param name="options">Pipeline options supplying candidate categories.</param>
    /// <param name="logger">Logger for diagnostics.</param>
    public ChatInsightGenerator(
        IChatClient chatClient,
        IOptions<DocumentProcessingOptions> options,
        ILogger<ChatInsightGenerator> logger)
    {
        ArgumentNullException.ThrowIfNull(chatClient);
        ArgumentNullException.ThrowIfNull(options);
        ArgumentNullException.ThrowIfNull(logger);
        _chatClient = chatClient;
        _options = options.Value;
        _logger = logger;
    }

    /// <inheritdoc />
    public async Task<DocumentInsights?> GenerateAsync(
        DocumentExtractionResult extraction,
        CancellationToken cancellationToken = default)
    {
        ArgumentNullException.ThrowIfNull(extraction);

        string categories = _options.InsightCategories.Count > 0
            ? string.Join(", ", _options.InsightCategories)
            : string.Join(", ", DefaultCategories);

        string prompt = BuildPrompt(extraction, categories);
        const string system =
            "You are a document-processing assistant. Respond with strict minified JSON matching " +
            "{\"summary\":string,\"category\":string,\"rationale\":string}. Do not use markdown.";

        try
        {
            string raw = await _chatClient.CompleteTextAsync(prompt, system, cancellationToken)
                .ConfigureAwait(false);
            return Parse(raw);
        }
        catch (Exception ex) when (ex is not OperationCanceledException)
        {
            Log.InsightGenerationFailed(_logger, ex);
            return null;
        }
    }

    private static string BuildPrompt(DocumentExtractionResult extraction, string categories)
    {
        IEnumerable<string> fieldLines = extraction.Fields.Select(f => $"- {f.Name}: {f.Value}");
        string fields = string.Join('\n', fieldLines);
        string content = extraction.Content.Length > MaxContentChars
            ? extraction.Content[..MaxContentChars]
            : extraction.Content;
        return $"Choose the best category from: {categories}.\n\nExtracted fields:\n{fields}\n\nDocument text:\n{content}";
    }

    private static DocumentInsights? Parse(string raw)
    {
        string? json = ExtractJson(raw);
        if (json is null)
        {
            return null;
        }

        try
        {
            using JsonDocument document = JsonDocument.Parse(json);
            JsonElement root = document.RootElement;
            if (root.ValueKind != JsonValueKind.Object)
            {
                return null;
            }

            string? summary = GetString(root, "summary");
            if (string.IsNullOrWhiteSpace(summary))
            {
                return null;
            }

            string category = GetString(root, "category") ?? "Other";
            string? rationale = GetString(root, "rationale");
            return new DocumentInsights(summary, category, rationale);
        }
        catch (JsonException)
        {
            return null;
        }
    }

    private static string? ExtractJson(string raw)
    {
        if (string.IsNullOrWhiteSpace(raw))
        {
            return null;
        }

        int start = raw.IndexOf('{', StringComparison.Ordinal);
        int end = raw.LastIndexOf('}');
        return start >= 0 && end > start ? raw[start..(end + 1)] : null;
    }

    private static string? GetString(JsonElement element, string name) =>
        element.TryGetProperty(name, out JsonElement value) && value.ValueKind == JsonValueKind.String
            ? value.GetString()
            : null;
}
