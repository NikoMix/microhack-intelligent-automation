// =============================================================================
// Lab 3 — Document Processing migration target
// Azure Functions (Flex Consumption, .NET 10 isolated) + Azure AI Document
// Intelligence, with identity-based connections (no storage keys), a review
// queue for the human-in-the-loop step, and workspace-based Application Insights.
//
// Deploy (resource-group scope):
//   az group create -n rg-lab3-doc -l swedencentral
//   az deployment group create -g rg-lab3-doc -f main.bicep -p main.bicepparam
//
// All authentication uses a user-assigned managed identity via Entra ID. No keys
// or connection strings are emitted by this template.
// =============================================================================

targetScope = 'resourceGroup'

// -----------------------------------------------------------------------------
// Parameters
// -----------------------------------------------------------------------------

@minLength(3)
@maxLength(11)
@description('Short lowercase alphanumeric prefix used to derive resource names.')
param namePrefix string = 'lab3doc'

@description('Azure region for all resources. Defaults to the resource group location.')
param location string = resourceGroup().location

@allowed([512, 2048, 4096])
@description('Per-instance memory (MB) for the Flex Consumption plan. 2048 (1 vCPU) is the default.')
param instanceMemoryMB int = 2048

@minValue(40)
@maxValue(1000)
@description('Maximum scale-out instance count for the Flex Consumption plan.')
param maximumInstanceCount int = 100

@allowed([
  'S0'
])
@description('SKU for Azure AI Document Intelligence. S0 is the standard paid tier; there is no free tier for the resource itself.')
param documentIntelligenceSku string = 'S0'

@description('Enable modular-inference LLM post-processing (summarize/classify). Requires inference provider settings to be supplied separately.')
param enableInsights bool = false

@description('Blob container that receives documents to process (blob trigger source).')
param incomingDocumentsContainerName string = 'incoming-documents'

@description('Blob container that holds the deployed application package for Flex Consumption.')
param deploymentStorageContainerName string = 'app-package'

@description('Storage queue used for the human-in-the-loop review/approval step.')
param reviewQueueName string = 'document-review'

@description('Optional resource tags applied to every resource.')
param tags object = {}

// -----------------------------------------------------------------------------
// Variables
// -----------------------------------------------------------------------------

var resourceToken = toLower(uniqueString(subscription().id, resourceGroup().id, namePrefix))

// Storage account names must be 3-24 chars, lowercase alphanumeric only.
// The derived value is always 18-24 chars ('st' + namePrefix[3-11] + 13-char token),
// but the analyzer can't infer the minimum through take()/replace().
var storageAccountName = take(toLower(replace('st${namePrefix}${resourceToken}', '-', '')), 24)
var functionAppName = '${namePrefix}-func-${resourceToken}'
var planName = '${namePrefix}-plan-${resourceToken}'
var documentIntelligenceName = '${namePrefix}-docintel-${resourceToken}'
var logAnalyticsName = '${namePrefix}-law-${resourceToken}'
var applicationInsightsName = '${namePrefix}-appi-${resourceToken}'
var managedIdentityName = '${namePrefix}-id-${resourceToken}'

// Built-in role definition IDs (verified against Azure RBAC docs).
var roleIds = {
  storageBlobDataOwner: 'b7e6dc6d-f1e8-4753-8033-0f276bb0955b'
  storageQueueDataContributor: '974c5e8b-45b9-4653-ba55-5f855dd0fb88'
  cognitiveServicesUser: 'a97b65f3-24c7-4388-baec-2e87135dc908'
  monitoringMetricsPublisher: '3913510d-42f4-4e42-8a64-420c390055eb'
}

// -----------------------------------------------------------------------------
// User-assigned managed identity (Entra ID auth for every connection)
// -----------------------------------------------------------------------------

resource managedIdentity 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = {
  name: managedIdentityName
  location: location
  tags: tags
}

// -----------------------------------------------------------------------------
// Observability: Log Analytics + workspace-based Application Insights
// -----------------------------------------------------------------------------

resource logAnalytics 'Microsoft.OperationalInsights/workspaces@2023-09-01' = {
  name: logAnalyticsName
  location: location
  tags: tags
  properties: {
    sku: {
      name: 'PerGB2018'
    }
    retentionInDays: 30
  }
}

resource applicationInsights 'Microsoft.Insights/components@2020-02-02' = {
  name: applicationInsightsName
  location: location
  tags: tags
  kind: 'web'
  properties: {
    Application_Type: 'web'
    WorkspaceResourceId: logAnalytics.id
    IngestionMode: 'LogAnalytics'
    publicNetworkAccessForIngestion: 'Enabled'
    publicNetworkAccessForQuery: 'Enabled'
  }
}

// -----------------------------------------------------------------------------
// Storage: deployment package container, incoming-documents container, review queue.
// Shared-key access is disabled — every connection is identity-based.
// -----------------------------------------------------------------------------

resource storageAccount 'Microsoft.Storage/storageAccounts@2024-01-01' = {
  // Derived name is always 18-24 chars; suppress the false-positive minimum-length warning.
  #disable-next-line BCP334
  name: storageAccountName
  location: location
  tags: tags
  kind: 'StorageV2'
  sku: {
    name: 'Standard_LRS'
  }
  properties: {
    accessTier: 'Hot'
    allowBlobPublicAccess: false
    allowSharedKeyAccess: false
    minimumTlsVersion: 'TLS1_2'
    supportsHttpsTrafficOnly: true
    dnsEndpointType: 'Standard'
    publicNetworkAccess: 'Enabled'
    networkAcls: {
      bypass: 'AzureServices'
      defaultAction: 'Allow'
    }
  }

  resource blobServices 'blobServices@2024-01-01' = {
    name: 'default'

    resource deploymentContainer 'containers@2024-01-01' = {
      name: deploymentStorageContainerName
      properties: {
        publicAccess: 'None'
      }
    }

    resource incomingContainer 'containers@2024-01-01' = {
      name: incomingDocumentsContainerName
      properties: {
        publicAccess: 'None'
      }
    }
  }

  resource queueServices 'queueServices@2024-01-01' = {
    name: 'default'

    resource reviewQueue 'queues@2024-01-01' = {
      name: reviewQueueName
    }
  }
}

// -----------------------------------------------------------------------------
// Azure AI Document Intelligence (kind FormRecognizer). customSubDomainName is
// required for Entra ID (token) authentication.
// -----------------------------------------------------------------------------

resource documentIntelligence 'Microsoft.CognitiveServices/accounts@2024-10-01' = {
  name: documentIntelligenceName
  location: location
  tags: tags
  kind: 'FormRecognizer'
  sku: {
    name: documentIntelligenceSku
  }
  properties: {
    customSubDomainName: documentIntelligenceName
    publicNetworkAccess: 'Enabled'
    disableLocalAuth: true
  }
}

// -----------------------------------------------------------------------------
// Flex Consumption plan + Function App (.NET 10 isolated)
// -----------------------------------------------------------------------------

resource plan 'Microsoft.Web/serverfarms@2024-04-01' = {
  name: planName
  location: location
  tags: tags
  kind: 'functionapp'
  sku: {
    tier: 'FlexConsumption'
    name: 'FC1'
  }
  properties: {
    reserved: true
  }
}

resource functionApp 'Microsoft.Web/sites@2024-04-01' = {
  name: functionAppName
  location: location
  tags: tags
  kind: 'functionapp,linux'
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${managedIdentity.id}': {}
    }
  }
  properties: {
    serverFarmId: plan.id
    httpsOnly: true
    siteConfig: {
      minTlsVersion: '1.2'
    }
    functionAppConfig: {
      deployment: {
        storage: {
          type: 'blobContainer'
          value: '${storageAccount.properties.primaryEndpoints.blob}${deploymentStorageContainerName}'
          authentication: {
            type: 'UserAssignedIdentity'
            userAssignedIdentityResourceId: managedIdentity.id
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
}

// App settings: all identity-based, no keys. The user-assigned identity client ID
// is supplied to DefaultAzureCredential via AZURE_CLIENT_ID so the pipeline's
// Document Intelligence client and approval-queue writer pick the right identity.
resource functionAppSettings 'Microsoft.Web/sites/config@2024-04-01' = {
  parent: functionApp
  name: 'appsettings'
  properties: {
    // Host storage (identity-based)
    AzureWebJobsStorage__accountName: storageAccount.name
    AzureWebJobsStorage__credential: 'managedidentity'
    AzureWebJobsStorage__clientId: managedIdentity.properties.clientId

    // Application Insights (Entra-authenticated telemetry)
    APPLICATIONINSIGHTS_CONNECTION_STRING: applicationInsights.properties.ConnectionString
    APPLICATIONINSIGHTS_AUTHENTICATION_STRING: 'Authorization=AAD;ClientId=${managedIdentity.properties.clientId}'

    // DefaultAzureCredential: select the user-assigned identity.
    AZURE_CLIENT_ID: managedIdentity.properties.clientId

    // Document Intelligence (Entra ID; no key).
    DocumentIntelligence__Endpoint: documentIntelligence.properties.endpoint

    // Modular-inference insights toggle (provider settings supplied separately).
    DocumentProcessing__EnableInsights: toLower(string(enableInsights))

    // Human-in-the-loop review queue.
    Approval__QueueName: reviewQueueName
    Approval__QueueServiceUri: storageAccount.properties.primaryEndpoints.queue
    Approval__Queue__queueServiceUri: storageAccount.properties.primaryEndpoints.queue
    Approval__Queue__credential: 'managedidentity'
    Approval__Queue__clientId: managedIdentity.properties.clientId
  }
  dependsOn: [
    blobDataOwnerAssignment
    queueDataContributorAssignment
    cognitiveServicesUserAssignment
    monitoringMetricsPublisherAssignment
  ]
}

// -----------------------------------------------------------------------------
// Role assignments (least privilege) for the user-assigned identity
// -----------------------------------------------------------------------------

resource blobDataOwnerAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(storageAccount.id, managedIdentity.id, roleIds.storageBlobDataOwner)
  scope: storageAccount
  properties: {
    principalId: managedIdentity.properties.principalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', roleIds.storageBlobDataOwner)
  }
}

resource queueDataContributorAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(storageAccount.id, managedIdentity.id, roleIds.storageQueueDataContributor)
  scope: storageAccount
  properties: {
    principalId: managedIdentity.properties.principalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', roleIds.storageQueueDataContributor)
  }
}

resource cognitiveServicesUserAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(documentIntelligence.id, managedIdentity.id, roleIds.cognitiveServicesUser)
  scope: documentIntelligence
  properties: {
    principalId: managedIdentity.properties.principalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', roleIds.cognitiveServicesUser)
  }
}

resource monitoringMetricsPublisherAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(applicationInsights.id, managedIdentity.id, roleIds.monitoringMetricsPublisher)
  scope: applicationInsights
  properties: {
    principalId: managedIdentity.properties.principalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', roleIds.monitoringMetricsPublisher)
  }
}

// -----------------------------------------------------------------------------
// Outputs
// -----------------------------------------------------------------------------

@description('Function App name.')
output functionAppName string = functionApp.name

@description('Function App default host name.')
output functionAppDefaultHostName string = functionApp.properties.defaultHostName

@description('Document Intelligence endpoint (Entra ID auth).')
output documentIntelligenceEndpoint string = documentIntelligence.properties.endpoint

@description('Storage account name.')
output storageAccountName string = storageAccount.name

@description('Blob container documents are uploaded to (blob trigger source).')
output incomingDocumentsContainerName string = incomingDocumentsContainerName

@description('Review/approval queue name (human-in-the-loop).')
output reviewQueueName string = reviewQueueName

@description('User-assigned managed identity client ID (used by DefaultAzureCredential).')
output managedIdentityClientId string = managedIdentity.properties.clientId

@description('User-assigned managed identity principal (object) ID.')
output managedIdentityPrincipalId string = managedIdentity.properties.principalId
