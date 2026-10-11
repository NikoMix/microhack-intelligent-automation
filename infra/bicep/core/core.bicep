targetScope = 'resourceGroup'

@description('Short workload identifier used as the base for shared platform resource names.')
@minLength(2)
@maxLength(12)
param workloadName string

@description('Deployment environment for the shared platform foundation.')
@allowed([
  'dev'
  'test'
  'prod'
])
param environment string

@description('Azure region for all shared platform resources.')
param location string = resourceGroup().location

@description('Optional numeric or short text instance discriminator for multiple lab deployments in the same resource group.')
@maxLength(4)
param instance string = '001'

@description('Tags applied to all shared platform resources.')
param tags object = {}

@description('Deploy a shared Key Vault for labs that need secret references or evidence-safe configuration.')
param deployKeyVault bool = true

@description('Allow Key Vault public access for training labs without private endpoints. Keep false for production.')
param keyVaultAllowPublicAccess bool = false

@description('Daily Log Analytics ingestion cap in GB as a JSON number string. Default 0.5 caps training lab cost; set -1 to disable the cap.')
param logAnalyticsDailyQuotaGb string = '0.5'

var standardTags = union(tags, {
  workload: workloadName
  environment: environment
  managedBy: 'bicep'
  course: 'microhack-intelligent-automation'
})

module naming '../modules/naming.bicep' = {
  name: 'naming'
  params: {
    workloadName: workloadName
    environment: environment
    location: location
    instance: instance
  }
}

module logAnalytics '../modules/logAnalytics.bicep' = {
  name: 'logAnalytics'
  params: {
    name: naming.outputs.names.logAnalytics
    location: location
    tags: standardTags
    dailyQuotaGb: logAnalyticsDailyQuotaGb
  }
}

module appInsights '../modules/appInsights.bicep' = {
  name: 'appInsights'
  params: {
    name: naming.outputs.names.appInsights
    location: location
    logAnalyticsWorkspaceId: logAnalytics.outputs.workspaceId
    tags: standardTags
  }
}

module managedIdentity '../modules/managedIdentity.bicep' = {
  name: 'managedIdentity'
  params: {
    name: naming.outputs.names.managedIdentity
    location: location
    tags: standardTags
  }
}

module keyVault '../modules/keyVault.bicep' = if (deployKeyVault) {
  name: 'keyVault'
  params: {
    name: naming.outputs.names.keyVault
    location: location
    tags: standardTags
    allowPublicAccess: keyVaultAllowPublicAccess
    diagnosticWorkspaceId: logAnalytics.outputs.workspaceId
  }
}

@description('Client ID of the platform user-assigned managed identity.')
output identityClientId string = managedIdentity.outputs.clientId

@description('Microsoft Entra principal ID of the platform user-assigned managed identity.')
output identityPrincipalId string = managedIdentity.outputs.principalId

@description('Application Insights connection string for OpenTelemetry and Azure SDK telemetry.')
output appInsightsConnectionString string = appInsights.outputs.connectionString

@description('Azure resource ID of the Log Analytics workspace.')
output logAnalyticsWorkspaceId string = logAnalytics.outputs.workspaceId

@description('Key Vault URI when Key Vault is deployed; otherwise an empty string.')
output keyVaultUri string = keyVault.?outputs.?vaultUri ?? ''

@description('Generated naming values used by the platform foundation.')
output names object = naming.outputs.names
