using System.Collections;
using System.Globalization;
using Azure;
using Azure.AI.DocumentIntelligence;
using Azure.Core;
using IAuto.DocumentProcessing.Configuration;
using IAuto.DocumentProcessing.Models;
using Microsoft.Extensions.Options;

namespace IAuto.DocumentProcessing.DocumentIntelligence;

public sealed class AzureDocumentInvoiceAnalyzer : IDocumentInvoiceAnalyzer
{
    private readonly DocumentIntelligenceClient _client;
    private readonly IInvoiceFieldMapper _mapper;
    private readonly DocumentProcessingOptions _options;

    public AzureDocumentInvoiceAnalyzer(
        TokenCredential credential,
        IOptions<DocumentProcessingOptions> options,
        IInvoiceFieldMapper mapper)
    {
        ArgumentNullException.ThrowIfNull(credential);
        ArgumentNullException.ThrowIfNull(options);
        ArgumentNullException.ThrowIfNull(mapper);

        _options = options.Value;
        _client = new DocumentIntelligenceClient(new Uri(_options.DocumentIntelligenceEndpoint), credential);
        _mapper = mapper;
    }

    public async Task<InvoiceAnalysis> AnalyzeInvoiceAsync(Stream document, string sourceBlobName, CancellationToken cancellationToken)
    {
        ArgumentNullException.ThrowIfNull(document);
        ArgumentException.ThrowIfNullOrWhiteSpace(sourceBlobName);

        if (document.CanSeek)
        {
            document.Position = 0;
        }

        Operation<AnalyzeResult> operation = await _client.AnalyzeDocumentAsync(
            WaitUntil.Completed,
            _options.DocumentIntelligenceModelId,
            BinaryData.FromStream(document),
            cancellationToken: cancellationToken).ConfigureAwait(false);

        var rawDocument = ConvertAnalyzeResult(operation.Value);
        return _mapper.Map(rawDocument);
    }

    private static RawInvoiceDocument ConvertAnalyzeResult(AnalyzeResult result)
    {
        var analyzedDocument = Enumerate(GetProperty(result, "Documents")).FirstOrDefault();
        if (analyzedDocument is null)
        {
            return new RawInvoiceDocument(new Dictionary<string, RawInvoiceField>(StringComparer.OrdinalIgnoreCase), Confidence: null);
        }

        var fields = ConvertFieldDictionary(GetProperty(analyzedDocument, "Fields"));
        return new RawInvoiceDocument(fields, ConvertToDouble(GetProperty(analyzedDocument, "Confidence")));
    }

    private static IReadOnlyDictionary<string, RawInvoiceField> ConvertFieldDictionary(object? fieldsObject)
    {
        var fields = new Dictionary<string, RawInvoiceField>(StringComparer.OrdinalIgnoreCase);
        foreach (var entry in Enumerate(fieldsObject))
        {
            var key = GetProperty(entry, "Key") as string;
            var value = GetProperty(entry, "Value");
            if (key is not null && value is not null)
            {
                fields[key] = ConvertField(value);
            }
        }

        return fields;
    }

    private static RawInvoiceField ConvertField(object field)
    {
        var currency = GetProperty(field, "ValueCurrency");
        var fieldObject = GetProperty(field, "ValueObject") ?? GetProperty(field, "ValueDictionary");
        var fieldArray = GetProperty(field, "ValueArray") ?? GetProperty(field, "ValueList");

        return new RawInvoiceField(
            Content: GetProperty(field, "Content") as string,
            StringValue: GetProperty(field, "ValueString") as string,
            NumberValue: ConvertToDecimal(GetProperty(field, "ValueDouble") ?? GetProperty(field, "ValueInt64")),
            DateValue: ConvertToDateOnly(GetProperty(field, "ValueDate")),
            CurrencyAmount: ConvertToDecimal(GetProperty(currency, "Amount")),
            CurrencyCode: GetProperty(currency, "CurrencyCode") as string,
            Confidence: ConvertToDouble(GetProperty(field, "Confidence")),
            ObjectValue: ConvertFieldDictionary(fieldObject),
            ArrayValue: Enumerate(fieldArray).Select(ConvertField).ToArray());
    }

    private static object? GetProperty(object? instance, string name) =>
        instance?.GetType().GetProperty(name)?.GetValue(instance);

    private static IEnumerable<object> Enumerate(object? value)
    {
        if (value is null || value is string)
        {
            yield break;
        }

        if (value is IEnumerable enumerable)
        {
            foreach (var item in enumerable)
            {
                if (item is not null)
                {
                    yield return item;
                }
            }
        }
    }

    private static decimal? ConvertToDecimal(object? value) => value switch
    {
        null => null,
        decimal decimalValue => decimalValue,
        double doubleValue => Convert.ToDecimal(doubleValue, CultureInfo.InvariantCulture),
        float floatValue => Convert.ToDecimal(floatValue, CultureInfo.InvariantCulture),
        int intValue => intValue,
        long longValue => longValue,
        _ when decimal.TryParse(Convert.ToString(value, CultureInfo.InvariantCulture), NumberStyles.Number, CultureInfo.InvariantCulture, out var parsed) => parsed,
        _ => null,
    };

    private static double? ConvertToDouble(object? value) => value switch
    {
        null => null,
        double doubleValue => doubleValue,
        float floatValue => floatValue,
        decimal decimalValue => Convert.ToDouble(decimalValue, CultureInfo.InvariantCulture),
        _ when double.TryParse(Convert.ToString(value, CultureInfo.InvariantCulture), NumberStyles.Float, CultureInfo.InvariantCulture, out var parsed) => parsed,
        _ => null,
    };

    private static DateOnly? ConvertToDateOnly(object? value) => value switch
    {
        null => null,
        DateOnly date => date,
        DateTime dateTime => DateOnly.FromDateTime(dateTime),
        DateTimeOffset dateTimeOffset => DateOnly.FromDateTime(dateTimeOffset.UtcDateTime),
        _ when DateOnly.TryParse(Convert.ToString(value, CultureInfo.InvariantCulture), CultureInfo.InvariantCulture, DateTimeStyles.None, out var parsed) => parsed,
        _ => null,
    };
}
