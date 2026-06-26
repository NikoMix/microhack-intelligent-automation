// Subscription-scoped entry point: creates the per-environment resource group and deploys the
// hybrid-integration workload into it. Deploy with:
//   az deployment sub create --location <region> --template-file main.bicep \
//     --parameters params/dev.bicepparam --parameters gitHubToken=... onPremApiKey=...
targetScope = 'subscription'

@description('Short prefix for resource names (lowercase letters/digits).')
@minLength(2)
@maxLength(10)
param namePrefix string = 'iauto'

@description('Deployment environment discriminator.')
@allowed([
  'dev'
  'test'
  'prod'
])
param environment string

@description('Primary Azure region for the resource group and resources.')
param location string = 'westeurope'

@description('Publisher email (required by API Management).')
param publisherEmail string

@description('Publisher organisation name.')
param publisherName string = 'Intelligent Automation TTT'

@description('Base URL of the on-prem stub the Connector calls.')
param onPremBaseUrl string

@description('Inference provider: github | azure_openai | foundry. Free GitHub Models by default.')
@allowed([
  'github'
  'azure_openai'
  'foundry'
])
param inferenceProvider string = 'github'

@description('Provider-specific, non-secret inference app settings merged into the Function.')
param inferenceAppSettings object = {}

@description('Enable Key Vault purge protection. Off in dev/test for easy lab reset; on in prod.')
param enablePurgeProtection bool = false

@description('Maximum Flex Consumption instance count (>=40).')
@minValue(40)
param functionMaxInstanceCount int = 40

@description('GitHub token (or provider key) stored in Key Vault. Supply at deploy time via --parameters; never commit. Empty default keeps what-if/param builds runnable.')
@secure()
param gitHubToken string = ''

@description('API key for the on-prem stub, stored in Key Vault. Supply at deploy time via --parameters; never commit. Empty default keeps what-if/param builds runnable.')
@secure()
param onPremApiKey string = ''

var tags = {
  workload: 'hybrid-integration'
  lab: 'lab-6'
  environment: environment
  managedBy: 'bicep'
}

resource resourceGroup 'Microsoft.Resources/resourceGroups@2024-03-01' = {
  name: 'rg-${namePrefix}-${environment}'
  location: location
  tags: tags
}

module workload 'workload.bicep' = {
  name: 'workload-${environment}'
  scope: resourceGroup
  params: {
    namePrefix: namePrefix
    environment: environment
    location: location
    publisherEmail: publisherEmail
    publisherName: publisherName
    onPremBaseUrl: onPremBaseUrl
    inferenceProvider: inferenceProvider
    inferenceAppSettings: inferenceAppSettings
    enablePurgeProtection: enablePurgeProtection
    functionMaxInstanceCount: functionMaxInstanceCount
    gitHubToken: gitHubToken
    onPremApiKey: onPremApiKey
    tags: tags
  }
}

@description('Name of the created resource group.')
output resourceGroupName string = resourceGroup.name

@description('API Management gateway URL (the hybrid front door).')
output apimGatewayUrl string = workload.outputs.apimGatewayUrl

@description('Connector Function app name.')
output functionAppName string = workload.outputs.functionAppName

@description('Logic App (Standard) name.')
output logicAppName string = workload.outputs.logicAppName

@description('Key Vault name holding the secrets consumed via managed identity.')
output keyVaultName string = workload.outputs.keyVaultName
