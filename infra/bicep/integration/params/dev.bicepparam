using '../main.bicep'

// Dev: cheapest footprint, purge protection off for easy reset between lab runs.
param environment = 'dev'
param namePrefix = 'iauto'
param location = 'westeurope'
param publisherEmail = 'ttt-trainer@contoso.com'
param publisherName = 'Intelligent Automation TTT'
param onPremBaseUrl = 'https://onprem-stub-dev.example.com'
param inferenceProvider = 'github'
param enablePurgeProtection = false
param functionMaxInstanceCount = 40

// Secrets (gitHubToken, onPremApiKey) are NOT set here. They are passed at deploy time:
//   az deployment sub create ... --parameters gitHubToken=$GH onPremApiKey=$KEY
