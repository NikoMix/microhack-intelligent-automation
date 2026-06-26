using '../main.bicep'

// Test: production-like wiring, purge protection still off so the environment can be torn
// down and rebuilt during a course without name-reservation conflicts.
param environment = 'test'
param namePrefix = 'iauto'
param location = 'westeurope'
param publisherEmail = 'ttt-trainer@contoso.com'
param publisherName = 'Intelligent Automation TTT'
param onPremBaseUrl = 'https://onprem-stub-test.example.com'
param inferenceProvider = 'github'
param enablePurgeProtection = false
param functionMaxInstanceCount = 40

// Secrets (gitHubToken, onPremApiKey) are passed at deploy time, never committed.
