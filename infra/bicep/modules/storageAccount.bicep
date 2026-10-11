targetScope = 'resourceGroup'

@description('Name of the storage account. Must be globally unique, lowercase, and 3-24 characters.')
@minLength(3)
@maxLength(24)
param name string

@description('Azure region for the storage account.')
param location string = resourceGroup().location

@description('Tags applied to the storage account.')
param tags object = {}

@description('Allow public network access so free-tier labs work without private endpoints. Production deployments should set this to false.')
param allowPublicNetworkAccess bool = true

resource storage 'Microsoft.Storage/storageAccounts@2025-01-01' = {
  name: name
  location: location
  tags: union(tags, {
    module: 'storageAccount'
  })
  sku: {
    name: 'Standard_LRS'
  }
  kind: 'StorageV2'
  properties: {
    minimumTlsVersion: 'TLS1_2'
    allowBlobPublicAccess: false
    allowSharedKeyAccess: false
    publicNetworkAccess: allowPublicNetworkAccess ? 'Enabled' : 'Disabled'
    supportsHttpsTrafficOnly: true
    defaultToOAuthAuthentication: true
    accessTier: 'Hot'
    networkAcls: {
      bypass: 'AzureServices'
      defaultAction: allowPublicNetworkAccess ? 'Allow' : 'Deny'
    }
    encryption: {
      keySource: 'Microsoft.Storage'
      services: {
        blob: {
          enabled: true
          keyType: 'Account'
        }
        file: {
          enabled: true
          keyType: 'Account'
        }
      }
    }
  }
}

@description('Name of the storage account.')
output name string = storage.name

@description('Azure resource ID of the storage account.')
output resourceId string = storage.id

@description('Primary Blob service endpoint for the storage account.')
output blobEndpoint string = storage.properties.primaryEndpoints.blob
