targetScope = 'resourceGroup'

@description('Short workload identifier used for shared core and integration resource names.')
@minLength(2)
@maxLength(12)
param workloadName string

@description('Deployment environment for the lab.')
@allowed([
  'dev'
  'test'
  'prod'
])
param environment string

@description('Azure region for the integration deployment.')
param location string = resourceGroup().location

@description('Optional discriminator for repeated lab deployments in one resource group.')
@maxLength(4)
param instance string = '006'

@description('Tags applied to all integration resources.')
param tags object = {}

@description('Publisher name for the API Management service.')
param apimPublisherName string = 'Intelligent Automation Trainers'

@description('Publisher email for the API Management service.')
param apimPublisherEmail string = 'trainers@example.com'

@description('Allow public network access for low-friction labs. Production should combine private networking with APIM internal mode.')
param allowPublicNetworkAccess bool = true

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
var uniqueSuffix = take(toLower(uniqueString(resourceGroup().id, 'integration', normalizedInstance)), 6)
var coreUniqueSuffix = take(toLower(uniqueString(resourceGroup().id)), 6)
var resourcePrefix = '${normalizedWorkload}-${normalizedEnvironment}-${locationAbbr}-${normalizedInstance}'
var compactPrefix = '${normalizedWorkload}${normalizedEnvironment}${locationAbbr}${normalizedInstance}'
var sharedIdentityName = take('id-${resourcePrefix}-${coreUniqueSuffix}', 128)
var sharedIdentityResourceId = resourceId('Microsoft.ManagedIdentity/userAssignedIdentities', sharedIdentityName)
var functionStorageName = take('st${compactPrefix}fn${uniqueSuffix}', 24)
var logicStorageName = take('st${compactPrefix}la${uniqueSuffix}', 24)
var functionDeploymentContainerName = 'function-releases'
var standardTags = union(tags, {
  workload: workloadName
  environment: environment
  managedBy: 'bicep'
  course: 'microhack-intelligent-automation'
  lab: 'lab-6'
  workloadArea: 'hybrid-integration'
})

module core '../core/core.bicep' = {
  name: 'integration-core'
  params: {
    workloadName: workloadName
    environment: environment
    location: location
    instance: instance
    tags: tags
    deployKeyVault: true
    keyVaultAllowPublicAccess: allowPublicNetworkAccess
  }
}


module functionStorage '../modules/storageAccount.bicep' = {
  name: 'integration-function-storage'
  params: {
    name: functionStorageName
    location: location
    tags: standardTags
    allowPublicNetworkAccess: allowPublicNetworkAccess
  }
}

module logicStorage '../modules/storageAccount.bicep' = {
  name: 'integration-logic-storage'
  params: {
    name: logicStorageName
    location: location
    tags: standardTags
    allowPublicNetworkAccess: allowPublicNetworkAccess
  }
}

module storageBlobContributor '../modules/roleAssignment.bicep' = {
  name: 'integration-storage-blob-contributor'
  params: {
    principalId: core.outputs.identityPrincipalId
    roleName: 'Storage Blob Data Contributor'
    principalType: 'ServicePrincipal'
  }
}

module monitoringPublisher '../modules/roleAssignment.bicep' = {
  name: 'integration-monitoring-publisher'
  params: {
    principalId: core.outputs.identityPrincipalId
    roleName: 'Monitoring Metrics Publisher'
    principalType: 'ServicePrincipal'
  }
}

resource functionDeploymentContainer 'Microsoft.Storage/storageAccounts/blobServices/containers@2025-01-01' = {
  name: '${functionStorageName}/default/${functionDeploymentContainerName}'
  properties: {
    publicAccess: 'None'
  }
}

resource functionPlan 'Microsoft.Web/serverfarms@2024-04-01' = {
  name: take('asp-${resourcePrefix}-fn-${uniqueSuffix}', 60)
  location: location
  tags: standardTags
  kind: 'functionapp'
  sku: {
    name: 'FC1'
    tier: 'FlexConsumption'
    size: 'FC1'
    family: 'FC'
    capacity: 0
  }
  properties: {
    reserved: true
  }
}

resource functionApp 'Microsoft.Web/sites@2024-04-01' = {
  name: take('func-${resourcePrefix}-${uniqueSuffix}', 60)
  location: location
  tags: standardTags
  kind: 'functionapp,linux'
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${sharedIdentityResourceId}': {}
    }
  }
  properties: {
    serverFarmId: functionPlan.id
    httpsOnly: true
    publicNetworkAccess: allowPublicNetworkAccess ? 'Enabled' : 'Disabled'
    functionAppConfig: {
      runtime: {
        name: 'dotnet-isolated'
        version: '10.0'
      }
      deployment: {
        storage: {
          type: 'blobContainer'
          value: '${functionStorage.outputs.blobEndpoint}${functionDeploymentContainerName}'
          authentication: {
            type: 'UserAssignedIdentity'
            userAssignedIdentityResourceId: sharedIdentityResourceId
          }
        }
      }
      scaleAndConcurrency: {
        maximumInstanceCount: 20
        instanceMemoryMB: 2048
      }
    }
    siteConfig: {
      minTlsVersion: '1.2'
      ftpsState: 'Disabled'
      appSettings: [
        {
          name: 'AzureWebJobsStorage__accountName'
          value: functionStorageName
        }
        {
          name: 'AzureWebJobsStorage__credential'
          value: 'managedidentity'
        }
        {
          name: 'AzureWebJobsStorage__clientId'
          value: core.outputs.identityClientId
        }
        {
          name: 'APPLICATIONINSIGHTS_CONNECTION_STRING'
          value: core.outputs.appInsightsConnectionString
        }
        {
          name: 'FUNCTIONS_WORKER_RUNTIME'
          value: 'dotnet-isolated'
        }
        {
          name: 'INFERENCE_PROVIDER'
          value: 'github'
        }
        {
          name: 'GITHUB_MODELS_ENDPOINT'
          value: 'https://models.github.ai/inference'
        }
        {
          name: 'GITHUB_MODELS_MODEL'
          value: 'openai/gpt-4o-mini'
        }
      ]
    }
  }
  dependsOn: [
    storageBlobContributor
    monitoringPublisher
  ]
}

resource logicPlan 'Microsoft.Web/serverfarms@2024-04-01' = {
  name: take('asp-${resourcePrefix}-logic-${uniqueSuffix}', 60)
  location: location
  tags: standardTags
  kind: 'elastic'
  sku: {
    name: 'WS1'
    tier: 'WorkflowStandard'
    size: 'WS1'
    family: 'WS'
    capacity: 1
  }
}

resource logicApp 'Microsoft.Web/sites@2024-04-01' = {
  name: take('logic-${resourcePrefix}-${uniqueSuffix}', 60)
  location: location
  tags: standardTags
  kind: 'workflowapp'
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${sharedIdentityResourceId}': {}
    }
  }
  properties: {
    serverFarmId: logicPlan.id
    httpsOnly: true
    publicNetworkAccess: allowPublicNetworkAccess ? 'Enabled' : 'Disabled'
    siteConfig: {
      minTlsVersion: '1.2'
      ftpsState: 'Disabled'
      appSettings: [
        {
          name: 'FUNCTIONS_EXTENSION_VERSION'
          value: '~4'
        }
        {
          name: 'FUNCTIONS_WORKER_RUNTIME'
          value: 'node'
        }
        {
          name: 'AzureWebJobsStorage__accountName'
          value: logicStorageName
        }
        {
          name: 'AzureWebJobsStorage__credential'
          value: 'managedidentity'
        }
        {
          name: 'AzureWebJobsStorage__clientId'
          value: core.outputs.identityClientId
        }
        {
          name: 'APP_KIND'
          value: 'workflowApp'
        }
        {
          name: 'APPLICATIONINSIGHTS_CONNECTION_STRING'
          value: core.outputs.appInsightsConnectionString
        }
        {
          name: 'BRIDGE_API_BASE_URL'
          value: 'https://${functionApp.properties.defaultHostName}'
        }
      ]
    }
  }
  dependsOn: [
    storageBlobContributor
  ]
}

resource apiManagement 'Microsoft.ApiManagement/service@2024-05-01' = {
  name: take('apim-${resourcePrefix}-${uniqueSuffix}', 50)
  location: location
  tags: standardTags
  sku: {
    name: 'Consumption'
    capacity: 0
  }
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${sharedIdentityResourceId}': {}
    }
  }
  properties: {
    publisherEmail: apimPublisherEmail
    publisherName: apimPublisherName
    publicNetworkAccess: allowPublicNetworkAccess ? 'Enabled' : 'Disabled'
  }
}

resource bridgeApi 'Microsoft.ApiManagement/service/apis@2024-05-01' = {
  parent: apiManagement
  name: 'integration-bridge'
  properties: {
    displayName: 'Integration Bridge'
    path: 'integration'
    protocols: [
      'https'
    ]
    serviceUrl: 'https://${functionApp.properties.defaultHostName}/api'
    subscriptionRequired: true
  }
}

resource processBusinessEventOperation 'Microsoft.ApiManagement/service/apis/operations@2024-05-01' = {
  parent: bridgeApi
  name: 'process-business-event'
  properties: {
    displayName: 'Process business event'
    method: 'POST'
    urlTemplate: '/business-events'
    request: {
      headers: [
        {
          name: 'x-correlation-id'
          required: false
          type: 'string'
        }
      ]
      representations: [
        {
          contentType: 'application/json'
        }
      ]
    }
    responses: [
      {
        statusCode: 200
        description: 'Standard event processed.'
      }
      {
        statusCode: 202
        description: 'High-priority event accepted for approval.'
      }
    ]
  }
}

resource bridgeApiPolicy 'Microsoft.ApiManagement/service/apis/policies@2024-05-01' = {
  parent: bridgeApi
  name: 'policy'
  properties: {
    format: 'rawxml'
    value: '''
<policies>
  <inbound>
    <base />
    <set-header name="x-correlation-id" exists-action="skip">
      <value>@(context.Request.Headers.GetValueOrDefault("x-correlation-id", Guid.NewGuid().ToString()))</value>
    </set-header>
    <rate-limit-by-key calls="60" renewal-period="60" counter-key="@(context.Subscription?.Key ?? context.Request.IpAddress)" />
    <authentication-managed-identity resource="api://AzureADTokenExchange" />
  </inbound>
  <backend>
    <base />
  </backend>
  <outbound>
    <base />
    <set-header name="x-correlation-id" exists-action="skip">
      <value>@(context.Request.Headers.GetValueOrDefault("x-correlation-id", context.Response.Headers.GetValueOrDefault("x-correlation-id", Guid.NewGuid().ToString())))</value>
    </set-header>
  </outbound>
  <on-error>
    <base />
  </on-error>
</policies>
'''
  }
}

@description('Function App host name that backs API Management.')
output functionHostName string = functionApp.properties.defaultHostName

@description('API Management gateway URL for the integration bridge.')
output apiManagementGatewayUrl string = apiManagement.properties.gatewayUrl

@description('Logic Apps Standard site host name.')
output logicAppHostName string = logicApp.properties.defaultHostName

@description('User-assigned managed identity client ID consumed by integration resources.')
output identityClientId string = core.outputs.identityClientId





