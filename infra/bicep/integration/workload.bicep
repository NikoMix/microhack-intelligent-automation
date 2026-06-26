@description('Short prefix for resource names (lowercase letters/digits).')
@minLength(2)
@maxLength(10)
param namePrefix string

@description('Deployment environment discriminator.')
@allowed([
  'dev'
  'test'
  'prod'
])
param environment string

@description('Primary Azure region.')
param location string

@description('Publisher email (required by API Management).')
param publisherEmail string

@description('Publisher organisation name.')
param publisherName string

@description('Base URL of the on-prem stub the Connector calls.')
param onPremBaseUrl string

@description('Inference provider: github | azure_openai | foundry.')
@allowed([
  'github'
  'azure_openai'
  'foundry'
])
param inferenceProvider string

@description('Provider-specific, non-secret inference app settings merged into the Function.')
param inferenceAppSettings object = {}

@description('Enable Key Vault purge protection (recommended in prod).')
param enablePurgeProtection bool

@description('Maximum Flex Consumption instance count (>=40).')
@minValue(40)
param functionMaxInstanceCount int

@description('GitHub token (or provider key) stored in Key Vault.')
@secure()
param gitHubToken string

@description('API key for the on-prem stub, stored in Key Vault.')
@secure()
param onPremApiKey string

@description('Resource tags applied to every resource.')
param tags object

var suffix = take(uniqueString(resourceGroup().id), 6)
var compact = '${namePrefix}${environment}'

module identity 'modules/identity.bicep' = {
  name: 'identity'
  params: {
    location: location
    name: 'id-${namePrefix}-${environment}'
    tags: tags
  }
}

module monitoring 'modules/monitoring.bicep' = {
  name: 'monitoring'
  params: {
    location: location
    logAnalyticsName: 'log-${namePrefix}-${environment}'
    appInsightsName: 'appi-${namePrefix}-${environment}'
    tags: tags
  }
}

module keyVault 'modules/keyvault.bicep' = {
  name: 'keyvault'
  params: {
    location: location
    name: take('kv-${compact}-${suffix}', 24)
    readerPrincipalId: identity.outputs.principalId
    enablePurgeProtection: enablePurgeProtection
    gitHubToken: gitHubToken
    onPremApiKey: onPremApiKey
    tags: tags
  }
}

module functionApp 'modules/function.bicep' = {
  name: 'function'
  params: {
    location: location
    functionAppName: 'func-${namePrefix}-${environment}-${suffix}'
    planName: 'plan-func-${namePrefix}-${environment}'
    storageAccountName: take('stf${compact}${suffix}', 24)
    userAssignedIdentityId: identity.outputs.id
    userAssignedIdentityClientId: identity.outputs.clientId
    userAssignedIdentityPrincipalId: identity.outputs.principalId
    appInsightsConnectionString: monitoring.outputs.appInsightsConnectionString
    keyVaultName: keyVault.outputs.name
    onPremBaseUrl: onPremBaseUrl
    inferenceProvider: inferenceProvider
    inferenceAppSettings: inferenceAppSettings
    maximumInstanceCount: functionMaxInstanceCount
    tags: tags
  }
}

module logicApp 'modules/logicapp.bicep' = {
  name: 'logicapp'
  params: {
    location: location
    logicAppName: 'logic-${namePrefix}-${environment}-${suffix}'
    planName: 'plan-logic-${namePrefix}-${environment}'
    storageAccountName: take('stl${compact}${suffix}', 24)
    userAssignedIdentityId: identity.outputs.id
    appInsightsConnectionString: monitoring.outputs.appInsightsConnectionString
    functionResourceId: functionApp.outputs.id
    functionDefaultHostName: functionApp.outputs.defaultHostName
    tags: tags
  }
}

module apim 'modules/apim.bicep' = {
  name: 'apim'
  params: {
    location: location
    name: 'apim-${namePrefix}-${environment}-${suffix}'
    publisherEmail: publisherEmail
    publisherName: publisherName
    logicAppDefaultHostName: logicApp.outputs.defaultHostName
    tags: tags
  }
}

@description('API Management gateway URL (the hybrid front door).')
output apimGatewayUrl string = apim.outputs.gatewayUrl

@description('Connector Function app name.')
output functionAppName string = functionApp.outputs.name

@description('Logic App (Standard) name.')
output logicAppName string = logicApp.outputs.name

@description('Key Vault name holding the github-token and onprem-api-key secrets.')
output keyVaultName string = keyVault.outputs.name
