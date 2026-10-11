targetScope = 'resourceGroup'

@description('Short workload identifier aligned with the shared core deployment.')
@minLength(2)
@maxLength(12)
param workloadName string

@description('Deployment environment aligned with the shared core deployment.')
@allowed([
  'dev'
  'test'
  'prod'
])
param environment string

@description('Azure region for Lab 3 resources.')
param location string = resourceGroup().location

@description('Optional instance discriminator aligned with the shared core deployment.')
@maxLength(4)
param instance string = '001'

@description('Tags applied to Lab 3 resources.')
param tags object = {}

@description('Client ID output from infra/bicep/core/core.bicep.')
param identityClientId string

@description('Principal ID output from infra/bicep/core/core.bicep.')
param identityPrincipalId string

@description('Application Insights connection string output from infra/bicep/core/core.bicep.')
param appInsightsConnectionString string

@description('Log Analytics workspace resource ID output from infra/bicep/core/core.bicep.')
param logAnalyticsWorkspaceId string

@description('Generated names object output from infra/bicep/core/core.bicep.')
param names object

@description('Document Intelligence SKU. F0 is lowest cost when available; switch to S0 where F0 capacity is unavailable.')
@allowed([
  'F0'
  'S0'
])
param documentIntelligenceSku string = 'F0'

@description('Allow public network access for classroom labs without private endpoints. Set false for production landing zones.')
param allowPublicNetworkAccess bool = true

@description('Maximum instances for the Flex Consumption Function App.')
@minValue(1)
@maxValue(100)
param maximumInstanceCount int = 20

@description('Flex Consumption instance memory in MB.')
@allowed([
  512
  2048
  4096
])
param instanceMemoryMB int = 2048

var normalizedWorkload = toLower(replace(replace(replace(workloadName, '-', ''), '_', ''), ' ', ''))
var normalizedEnvironment = toLower(environment)
var normalizedInstance = toLower(replace(replace(replace(instance, '-', ''), '_', ''), ' ', ''))
var uniqueSuffix = take(toLower(uniqueString(resourceGroup().id, workloadName, environment, instance, 'docint')), 6)
var compactPrefix = take('${normalizedWorkload}${normalizedEnvironment}${normalizedInstance}', 12)
var standardTags = union(tags, {
  workload: workloadName
  environment: environment
  lab: 'lab-3'
  managedBy: 'bicep'
  course: 'microhack-intelligent-automation'
})
var functionStorageName = take('st${compactPrefix}fn${uniqueSuffix}', 24)
var dataStorageName = take('st${compactPrefix}doc${uniqueSuffix}', 24)
var functionAppName = take('func-${workloadName}-${environment}-doc-${uniqueSuffix}', 60)
var planName = take('asp-${workloadName}-${environment}-doc-${uniqueSuffix}', 40)
var docIntelligenceName = take('di-${workloadName}-${environment}-${uniqueSuffix}', 64)
var packageContainerName = 'app-package'
var incomingContainerName = 'incoming'
var processedContainerName = 'processed'
var storageSuffix = az.environment().suffixes.storage

resource sharedIdentity 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' existing = {
  name: names.managedIdentity
}

module functionStorage '../modules/storageAccount.bicep' = {
  name: 'functionStorage'
  params: {
    name: functionStorageName
    location: location
    tags: standardTags
    allowPublicNetworkAccess: allowPublicNetworkAccess
  }
}

module dataStorage '../modules/storageAccount.bicep' = {
  name: 'dataStorage'
  params: {
    name: dataStorageName
    location: location
    tags: standardTags
    allowPublicNetworkAccess: allowPublicNetworkAccess
  }
}

resource packageContainer 'Microsoft.Storage/storageAccounts/blobServices/containers@2025-01-01' = {
  name: '${functionStorageName}/default/${packageContainerName}'
  properties: {
    publicAccess: 'None'
  }
  dependsOn: [
    functionStorage
  ]
}

resource incomingContainer 'Microsoft.Storage/storageAccounts/blobServices/containers@2025-01-01' = {
  name: '${dataStorageName}/default/${incomingContainerName}'
  properties: {
    publicAccess: 'None'
  }
  dependsOn: [
    dataStorage
  ]
}

resource processedContainer 'Microsoft.Storage/storageAccounts/blobServices/containers@2025-01-01' = {
  name: '${dataStorageName}/default/${processedContainerName}'
  properties: {
    publicAccess: 'None'
  }
  dependsOn: [
    dataStorage
  ]
}

resource documentIntelligence 'Microsoft.CognitiveServices/accounts@2024-10-01' = {
  name: docIntelligenceName
  location: location
  tags: union(standardTags, {
    workloadComponent: 'document-intelligence'
  })
  kind: 'FormRecognizer'
  sku: {
    name: documentIntelligenceSku
  }
  properties: {
    customSubDomainName: docIntelligenceName
    publicNetworkAccess: allowPublicNetworkAccess ? 'Enabled' : 'Disabled'
    disableLocalAuth: true
    networkAcls: {
      defaultAction: allowPublicNetworkAccess ? 'Allow' : 'Deny'
      virtualNetworkRules: []
      ipRules: []
    }
  }
}

resource plan 'Microsoft.Web/serverfarms@2024-04-01' = {
  name: planName
  location: location
  tags: standardTags
  kind: 'functionapp'
  sku: {
    name: 'FC1'
    tier: 'FlexConsumption'
    size: 'FC1'
  }
  properties: {
    reserved: true
  }
}

module storageBlobContributor '../modules/roleAssignment.bicep' = {
  name: 'storageBlobContributor'
  params: {
    principalId: identityPrincipalId
    roleName: 'Storage Blob Data Contributor'
    principalType: 'ServicePrincipal'
  }
}

module documentIntelligenceUser '../modules/roleAssignment.bicep' = {
  name: 'documentIntelligenceUser'
  params: {
    principalId: identityPrincipalId
    roleDefinitionId: 'a97b65f3-24c7-4388-baec-2e87135dc908'
    principalType: 'ServicePrincipal'
  }
}

resource functionApp 'Microsoft.Web/sites@2024-04-01' = {
  name: functionAppName
  location: location
  tags: union(standardTags, {
    workloadComponent: 'document-processing-function'
  })
  kind: 'functionapp,linux'
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${sharedIdentity.id}': {}
    }
  }
  properties: {
    serverFarmId: plan.id
    httpsOnly: true
    publicNetworkAccess: allowPublicNetworkAccess ? 'Enabled' : 'Disabled'
    functionAppConfig: {
      deployment: {
        storage: {
          type: 'blobContainer'
          value: '${functionStorage.outputs.blobEndpoint}${packageContainerName}'
          authentication: {
            type: 'UserAssignedIdentity'
            userAssignedIdentityResourceId: sharedIdentity.id
          }
        }
      }
      runtime: {
        name: 'dotnet-isolated'
        version: '10.0'
      }
      scaleAndConcurrency: {
        maximumInstanceCount: maximumInstanceCount
        instanceMemoryMB: instanceMemoryMB
      }
    }
    siteConfig: {
      appSettings: [
        { name: 'FUNCTIONS_WORKER_RUNTIME', value: 'dotnet-isolated' }
        { name: 'APPLICATIONINSIGHTS_CONNECTION_STRING', value: appInsightsConnectionString }
        { name: 'AzureWebJobsStorage__blobServiceUri', value: functionStorage.outputs.blobEndpoint }
        { name: 'AzureWebJobsStorage__queueServiceUri', value: 'https://${functionStorage.outputs.name}.queue.${storageSuffix}/' }
        { name: 'AzureWebJobsStorage__tableServiceUri', value: 'https://${functionStorage.outputs.name}.table.${storageSuffix}/' }
        { name: 'AzureWebJobsStorage__clientId', value: identityClientId }
        { name: 'DocumentStorage__blobServiceUri', value: dataStorage.outputs.blobEndpoint }
        { name: 'DocumentStorage__clientId', value: identityClientId }
        { name: 'DocumentProcessing__StorageBlobServiceUri', value: dataStorage.outputs.blobEndpoint }
        { name: 'DocumentProcessing__DocumentIntelligenceEndpoint', value: documentIntelligence.properties.endpoint }
        { name: 'DocumentProcessing__IncomingContainer', value: incomingContainerName }
        { name: 'DocumentProcessing__ProcessedContainer', value: processedContainerName }
        { name: 'DocumentProcessing__DocumentIntelligenceModelId', value: 'prebuilt-invoice' }
        { name: 'INFERENCE_PROVIDER', value: 'github' }
        { name: 'GITHUB_MODELS_ENDPOINT', value: 'https://models.github.ai/inference' }
        { name: 'GITHUB_MODELS_MODEL', value: 'openai/gpt-4o-mini' }
      ]
      ftpsState: 'Disabled'
      minTlsVersion: '1.2'
      alwaysOn: false
    }
  }
  dependsOn: [
    packageContainer
    incomingContainer
    processedContainer
    storageBlobContributor
    documentIntelligenceUser
  ]
}

@description('Function App name for deployment and smoke tests.')
output functionAppName string = functionApp.name

@description('Document Intelligence endpoint used by the Function App.')
output documentIntelligenceEndpoint string = documentIntelligence.properties.endpoint

@description('Data storage Blob endpoint containing incoming and processed containers.')
output dataStorageBlobEndpoint string = dataStorage.outputs.blobEndpoint

@description('Incoming invoice container name.')
output incomingContainerName string = incomingContainerName

@description('Processed JSON output container name.')
output processedContainerName string = processedContainerName

@description('Log Analytics workspace connected through the shared core.')
output logAnalyticsWorkspaceId string = logAnalyticsWorkspaceId
