targetScope = 'resourceGroup'

@description('Short workload identifier used as the base for shared platform resource names.')
@minLength(2)
@maxLength(12)
param workloadName string

@description('Deployment environment for the shared platform foundation and Foundry/Search resources.')
@allowed([
  'dev'
  'test'
  'prod'
])
param environment string

@description('Azure region for all lab resources.')
param location string = resourceGroup().location

@description('Optional numeric or short text instance discriminator for multiple lab deployments.')
@maxLength(4)
param instance string = '001'

@description('Tags applied to all lab resources.')
param tags object = {}

@description('Azure AI Search SKU. Use free for lowest-cost labs when the subscription quota allows one free service; otherwise use basic.')
@allowed([
  'free'
  'basic'
])
param searchSku string = 'free'

@description('Logical Azure AI Search index name used by the Python ingestion script.')
param searchIndexName string = 'iauto-foundry-kb'

@description('Deploy a shared Key Vault through the core foundation.')
param deployKeyVault bool = true

@description('Allow Key Vault public access for training labs without private endpoints. Keep false for production.')
param keyVaultAllowPublicAccess bool = false

@description('Daily Log Analytics ingestion cap in GB as a JSON number string.')
param logAnalyticsDailyQuotaGb string = '0.5'

var normalizedWorkload = toLower(replace(replace(replace(replace(workloadName, '-', ''), '_', ''), ' ', ''), '.', ''))
var normalizedEnvironment = toLower(environment)
var normalizedInstance = toLower(replace(replace(replace(replace(instance, '-', ''), '_', ''), ' ', ''), '.', ''))
var locationAbbreviations = {
  swedencentral: 'sec'
  westeurope: 'weu'
  northeurope: 'neu'
  eastus: 'eus'
  eastus2: 'eus2'
  westus: 'wus'
  westus2: 'wus2'
  centralus: 'cus'
  uksouth: 'uks'
  ukwest: 'ukw'
}
var normalizedLocation = toLower(replace(replace(location, ' ', ''), '-', ''))
var locationAbbr = locationAbbreviations[?normalizedLocation] ?? take(normalizedLocation, 5)
var coreShortSuffix = take(toLower(uniqueString(resourceGroup().id)), 6)
var coreResourcePrefix = '${normalizedWorkload}-${normalizedEnvironment}-${locationAbbr}-${normalizedInstance}'
var platformIdentityName = take('id-${coreResourcePrefix}-${coreShortSuffix}', 128)
var uniqueSuffix = take(toLower(uniqueString(resourceGroup().id, normalizedWorkload, normalizedEnvironment, normalizedInstance)), 6)
var compactName = take('${normalizedWorkload}${normalizedEnvironment}${normalizedInstance}${uniqueSuffix}', 24)
var standardTags = union(tags, {
  workload: workloadName
  environment: environment
  managedBy: 'bicep'
  course: 'microhack-intelligent-automation'
  lab: 'lab-4-foundry-search'
})

module core '../core/core.bicep' = {
  name: 'core-foundation'
  params: {
    workloadName: workloadName
    environment: environment
    location: location
    instance: instance
    tags: tags
    deployKeyVault: deployKeyVault
    keyVaultAllowPublicAccess: keyVaultAllowPublicAccess
    logAnalyticsDailyQuotaGb: logAnalyticsDailyQuotaGb
  }
}

resource platformIdentity 'Microsoft.ManagedIdentity/userAssignedIdentities@2024-11-30' existing = {
  name: platformIdentityName
}

resource searchService 'Microsoft.Search/searchServices@2025-05-01' = {
  name: take('srch-${normalizedWorkload}-${normalizedEnvironment}-${normalizedInstance}-${uniqueSuffix}', 60)
  location: location
  tags: union(standardTags, {
    module: 'foundry-search'
  })
  sku: {
    name: searchSku
  }
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${platformIdentity.id}': {}
    }
  }
  properties: {
    authOptions: {
      aadOrApiKey: {
        aadAuthFailureMode: 'http401WithBearerChallenge'
      }
    }
    disableLocalAuth: true
    hostingMode: 'Default'
    partitionCount: 1
    publicNetworkAccess: 'Enabled'
    replicaCount: 1
  }
}

resource aiAccount 'Microsoft.CognitiveServices/accounts@2025-06-01' = {
  name: take('ais-${normalizedWorkload}-${normalizedEnvironment}-${normalizedInstance}-${uniqueSuffix}', 64)
  location: location
  tags: union(standardTags, {
    module: 'foundry-ai-services'
  })
  kind: 'AIServices'
  sku: {
    name: 'S0'
  }
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${platformIdentity.id}': {}
    }
  }
  properties: {
    allowProjectManagement: true
    customSubDomainName: take('ais-${compactName}', 64)
    disableLocalAuth: true
    dynamicThrottlingEnabled: true
    publicNetworkAccess: 'Enabled'
    restrictOutboundNetworkAccess: false
  }
}

resource foundryProject 'Microsoft.CognitiveServices/accounts/projects@2025-06-01' = {
  parent: aiAccount
  name: take('proj-${normalizedWorkload}-${normalizedEnvironment}-${normalizedInstance}', 64)
  location: location
  tags: union(standardTags, {
    module: 'foundry-project'
  })
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${platformIdentity.id}': {}
    }
  }
  properties: {
    displayName: 'Lab 4 Foundry Knowledge Agent'
    description: 'Azure AI Foundry project for migrating a Copilot Studio knowledge agent to Agent Framework RAG.'
  }
}

module cognitiveOpenAiUser '../modules/roleAssignment.bicep' = {
  name: 'ra-cognitive-openai-user'
  params: {
    principalId: core.outputs.identityPrincipalId
    roleName: 'Cognitive Services OpenAI User'
    principalType: 'ServicePrincipal'
  }
}

module searchIndexReader '../modules/roleAssignment.bicep' = {
  name: 'ra-search-index-reader'
  params: {
    principalId: core.outputs.identityPrincipalId
    roleDefinitionId: '1407120a-92aa-4202-b7e9-c0e197c71c8f'
    principalType: 'ServicePrincipal'
  }
}

module searchIndexContributor '../modules/roleAssignment.bicep' = {
  name: 'ra-search-index-contributor'
  params: {
    principalId: core.outputs.identityPrincipalId
    roleDefinitionId: '8ebe5a00-799e-43f5-93ac-243d3dce84a7'
    principalType: 'ServicePrincipal'
  }
}

module searchServiceContributor '../modules/roleAssignment.bicep' = {
  name: 'ra-search-service-contributor'
  params: {
    principalId: core.outputs.identityPrincipalId
    roleDefinitionId: '7ca78c08-252a-4471-8644-bb5ff32d4ba0'
    principalType: 'ServicePrincipal'
  }
}

@description('Azure AI Search endpoint for AZURE_SEARCH_ENDPOINT.')
output searchEndpoint string = 'https://${searchService.name}.search.windows.net'

@description('Azure AI Search index name for AZURE_SEARCH_INDEX.')
output searchIndex string = searchIndexName

@description('Azure AI Services / Foundry account name.')
output aiServicesAccountName string = aiAccount.name

@description('Azure AI Foundry project name.')
output foundryProjectName string = foundryProject.name

@description('Azure AI Foundry project endpoint for AZURE_AI_FOUNDRY_PROJECT_ENDPOINT.')
output foundryProjectEndpoint string = '${aiAccount.properties.endpoint}/api/projects/${foundryProject.name}'

@description('Application Insights connection string from shared core for APPLICATIONINSIGHTS_CONNECTION_STRING.')
output appInsightsConnectionString string = core.outputs.appInsightsConnectionString

@description('Platform managed identity client ID from shared core.')
output identityClientId string = core.outputs.identityClientId

@description('Platform managed identity principal ID from shared core.')
output identityPrincipalId string = core.outputs.identityPrincipalId
