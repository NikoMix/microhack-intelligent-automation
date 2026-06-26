using 'main.bicep'

param workloadName = 'iauto'
param environment = 'dev'
param location = 'swedencentral'
param instance = '003'
param tags = {
  purpose: 'train-the-trainer-lab-3'
}

// Replace these values with outputs from infra/bicep/core/core.bicep.
param identityClientId = '<core-identity-client-id>'
param identityPrincipalId = '<core-identity-principal-id>'
param appInsightsConnectionString = '<core-application-insights-connection-string>'
param logAnalyticsWorkspaceId = '<core-log-analytics-workspace-resource-id>'
param names = {
  managedIdentity: '<core-managed-identity-name>'
}

param documentIntelligenceSku = 'F0'
param allowPublicNetworkAccess = true
