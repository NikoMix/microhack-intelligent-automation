@description('Azure region for the Function app and its dependencies.')
param location string

@description('Globally unique Function app name.')
param functionAppName string

@description('Name of the Flex Consumption plan.')
param planName string

@description('Globally unique storage account name (deployment + runtime, keyless).')
@maxLength(24)
param storageAccountName string

@description('Resource ID of the user-assigned managed identity.')
param userAssignedIdentityId string

@description('Client ID of the user-assigned managed identity.')
param userAssignedIdentityClientId string

@description('Principal ID of the user-assigned managed identity (for storage role assignments).')
param userAssignedIdentityPrincipalId string

@description('Application Insights connection string.')
param appInsightsConnectionString string

@description('Key Vault name used to resolve secret references.')
param keyVaultName string

@description('Base URL of the on-prem stub the Connector calls.')
param onPremBaseUrl string

@description('Inference provider: github | azure_openai | foundry.')
param inferenceProvider string

@description('Provider-specific, non-secret inference app settings merged into the Function.')
param inferenceAppSettings object = {}

@description('Maximum Flex Consumption instance count (>=40).')
@minValue(40)
param maximumInstanceCount int = 40

@description('Per-instance memory in MB.')
@allowed([2048, 4096])
param instanceMemoryMB int = 2048

@description('Resource tags.')
param tags object = {}

// Built-in storage roles required by the Flex Consumption host (keyless / managed identity).
var storageBlobDataOwnerRoleId = 'b7e6dc6d-f1e8-4753-8033-0f276bb0955b'
var storageBlobDataContributorRoleId = 'ba92f5b4-2d11-453d-a403-e96b0029c9fe'
var storageQueueDataContributorRoleId = '974c5e8b-45b9-4653-ba55-5f855dd0fb88'
var deploymentContainerName = 'app-package'

resource storage 'Microsoft.Storage/storageAccounts@2023-05-01' = {
  name: storageAccountName
  location: location
  kind: 'StorageV2'
  sku: {
    name: 'Standard_LRS'
  }
  tags: tags
  properties: {
    accessTier: 'Hot'
    allowBlobPublicAccess: false
    allowSharedKeyAccess: false
    minimumTlsVersion: 'TLS1_2'
    supportsHttpsTrafficOnly: true
    publicNetworkAccess: 'Enabled'
    networkAcls: {
      bypass: 'AzureServices'
      defaultAction: 'Allow'
    }
  }

  resource blobServices 'blobServices' = {
    name: 'default'

    resource deploymentContainer 'containers' = {
      name: deploymentContainerName
      properties: {
        publicAccess: 'None'
      }
    }
  }
}

resource blobOwnerAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(storage.id, userAssignedIdentityPrincipalId, storageBlobDataOwnerRoleId)
  scope: storage
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', storageBlobDataOwnerRoleId)
    principalId: userAssignedIdentityPrincipalId
    principalType: 'ServicePrincipal'
  }
}

resource blobContributorAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(storage.id, userAssignedIdentityPrincipalId, storageBlobDataContributorRoleId)
  scope: storage
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', storageBlobDataContributorRoleId)
    principalId: userAssignedIdentityPrincipalId
    principalType: 'ServicePrincipal'
  }
}

resource queueContributorAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(storage.id, userAssignedIdentityPrincipalId, storageQueueDataContributorRoleId)
  scope: storage
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', storageQueueDataContributorRoleId)
    principalId: userAssignedIdentityPrincipalId
    principalType: 'ServicePrincipal'
  }
}

resource plan 'Microsoft.Web/serverfarms@2024-04-01' = {
  name: planName
  location: location
  kind: 'functionapp'
  tags: tags
  sku: {
    tier: 'FlexConsumption'
    name: 'FC1'
  }
  properties: {
    reserved: true
  }
}

// Non-secret base settings. Secrets (onprem-api-key, github-token) flow in as Key Vault
// references so they are never embedded in the template or the app configuration.
var baseAppSettings = {
  AzureWebJobsStorage__accountName: storage.name
  AzureWebJobsStorage__credential: 'managedidentity'
  AzureWebJobsStorage__clientId: userAssignedIdentityClientId
  APPLICATIONINSIGHTS_CONNECTION_STRING: appInsightsConnectionString
  ONPREM_BASE_URL: onPremBaseUrl
  ONPREM_API_KEY: '@Microsoft.KeyVault(VaultName=${keyVaultName};SecretName=onprem-api-key)'
  INFERENCE_PROVIDER: inferenceProvider
  GITHUB_TOKEN: '@Microsoft.KeyVault(VaultName=${keyVaultName};SecretName=github-token)'
}

resource functionApp 'Microsoft.Web/sites@2024-04-01' = {
  name: functionAppName
  location: location
  kind: 'functionapp,linux'
  tags: tags
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${userAssignedIdentityId}': {}
    }
  }
  properties: {
    serverFarmId: plan.id
    httpsOnly: true
    keyVaultReferenceIdentity: userAssignedIdentityId
    siteConfig: {
      minTlsVersion: '1.2'
    }
    functionAppConfig: {
      deployment: {
        storage: {
          type: 'blobContainer'
          value: '${storage.properties.primaryEndpoints.blob}${deploymentContainerName}'
          authentication: {
            type: 'UserAssignedIdentity'
            userAssignedIdentityResourceId: userAssignedIdentityId
          }
        }
      }
      scaleAndConcurrency: {
        maximumInstanceCount: maximumInstanceCount
        instanceMemoryMB: instanceMemoryMB
      }
      runtime: {
        name: 'dotnet-isolated'
        version: '10'
      }
    }
  }

  resource appSettings 'config' = {
    name: 'appsettings'
    properties: union(baseAppSettings, inferenceAppSettings)
  }

  dependsOn: [
    blobOwnerAssignment
    blobContributorAssignment
    queueContributorAssignment
  ]
}

@description('Function app name.')
output name string = functionApp.name

@description('Function app resource ID (used by callers to read host keys at deploy time).')
output id string = functionApp.id

@description('Default host name of the Function app.')
output defaultHostName string = functionApp.properties.defaultHostName
