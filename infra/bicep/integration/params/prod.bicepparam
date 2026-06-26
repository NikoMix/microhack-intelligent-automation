using '../main.bicep'

// Prod: hardened. Purge protection ON and a higher scale ceiling. Switch the inference
// provider to Azure OpenAI or Foundry by setting inferenceProvider + inferenceAppSettings
// (non-secret endpoints/models); the matching key still flows via Key Vault.
param environment = 'prod'
param namePrefix = 'iauto'
param location = 'westeurope'
param publisherEmail = 'ttt-trainer@contoso.com'
param publisherName = 'Intelligent Automation TTT'
param onPremBaseUrl = 'https://onprem-stub.example.com'
param inferenceProvider = 'github'
param enablePurgeProtection = true
param functionMaxInstanceCount = 100

// Example: keep GitHub Models but pin a model, or switch provider entirely.
// param inferenceProvider = 'azure_openai'
// param inferenceAppSettings = {
//   AZURE_OPENAI_ENDPOINT: 'https://my-aoai.openai.azure.com/'
//   AZURE_OPENAI_DEPLOYMENT: 'gpt-4o-mini'
// }

// Secrets (gitHubToken, onPremApiKey) are passed at deploy time, never committed.
