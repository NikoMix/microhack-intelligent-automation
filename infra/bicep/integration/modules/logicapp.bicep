@description('Azure region for the Logic App and its storage.')
param location string

@description('Globally unique Logic App (Standard) name.')
param logicAppName string

@description('Name of the WorkflowStandard (WS1) plan.')
param planName string

@description('Globally unique storage account name backing the Logic App content share.')
@maxLength(24)
param storageAccountName string

@description('Resource ID of the user-assigned managed identity.')
param userAssignedIdentityId string

@description('Application Insights connection string.')
param appInsightsConnectionString string

@description('Resource ID of the Connector Function app (used to read its host key at deploy time).')
param functionResourceId string

@description('Default host name of the Connector Function app.')
param functionDefaultHostName string

@description('Resource tags.')
param tags object = {}

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
    // Logic Apps Standard resolves its content share over the file endpoint with a shared key.
    // Keyless content-share is not yet a supported path, so this account keeps key access on
    // (the Function tier above demonstrates the fully keyless managed-identity pattern).
    allowSharedKeyAccess: true
    minimumTlsVersion: 'TLS1_2'
    supportsHttpsTrafficOnly: true
    publicNetworkAccess: 'Enabled'
    networkAcls: {
      bypass: 'AzureServices'
      defaultAction: 'Allow'
    }
  }
}

resource plan 'Microsoft.Web/serverfarms@2024-04-01' = {
  name: planName
  location: location
  kind: 'elastic'
  tags: tags
  sku: {
    name: 'WS1'
    tier: 'WorkflowStandard'
  }
  properties: {
    targetWorkerCount: 1
    targetWorkerSizeId: 3
    maximumElasticWorkerCount: 20
  }
}

var storageConnectionString = 'DefaultEndpointsProtocol=https;AccountName=${storage.name};EndpointSuffix=${environment().suffixes.storage};AccountKey=${storage.listKeys().keys[0].value}'

// Resolved at deploy time once the Function exists. The key is sent by the workflow as the
// x-functions-key header, so the on-prem system is only reachable through the Function.
var functionHostKey = listKeys('${functionResourceId}/host/default', '2024-04-01').functionKeys.default

resource logicApp 'Microsoft.Web/sites@2024-04-01' = {
  name: logicAppName
  location: location
  kind: 'functionapp,workflowapp'
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
    siteConfig: {
      minTlsVersion: '1.2'
      appSettings: [
        {
          name: 'APP_KIND'
          value: 'workflowApp'
        }
        {
          name: 'FUNCTIONS_EXTENSION_VERSION'
          value: '~4'
        }
        {
          name: 'FUNCTIONS_WORKER_RUNTIME'
          value: 'dotnet'
        }
        {
          name: 'AzureWebJobsStorage'
          value: storageConnectionString
        }
        {
          name: 'WEBSITE_CONTENTAZUREFILECONNECTIONSTRING'
          value: storageConnectionString
        }
        {
          name: 'WEBSITE_CONTENTSHARE'
          value: toLower(logicAppName)
        }
        {
          name: 'APPLICATIONINSIGHTS_CONNECTION_STRING'
          value: appInsightsConnectionString
        }
        {
          name: 'FUNCTION_ENRICH_ORDER_URL'
          value: 'https://${functionDefaultHostName}/api/enrich-order'
        }
        {
          name: 'FUNCTION_HOST_KEY'
          value: functionHostKey
        }
      ]
    }
  }
}

@description('Logic App (Standard) name.')
output name string = logicApp.name

@description('Default host name of the Logic App.')
output defaultHostName string = logicApp.properties.defaultHostName
