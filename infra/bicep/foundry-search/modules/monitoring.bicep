// Log Analytics workspace + workspace-based Application Insights.
// Supplies the connection string the agent's OpenTelemetry exporter sends traces/metrics to.
metadata description = 'Log Analytics workspace and workspace-based Application Insights for OpenTelemetry.'

@description('Azure region for the monitoring resources.')
param location string

@description('Name of the Log Analytics workspace.')
param logAnalyticsName string

@description('Name of the Application Insights component.')
param applicationInsightsName string

@description('Tags applied to all resources.')
param tags object = {}

@description('Daily ingestion cap (GB) to protect lab spend. Set to -1 to remove the cap.')
param dailyQuotaGb int = 1

resource logAnalytics 'Microsoft.OperationalInsights/workspaces@2023-09-01' = {
  name: logAnalyticsName
  location: location
  tags: tags
  properties: {
    sku: {
      name: 'PerGB2018'
    }
    retentionInDays: 30
    workspaceCapping: {
      dailyQuotaGb: dailyQuotaGb
    }
    features: {
      enableLogAccessUsingOnlyResourcePermissions: true
    }
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

@description('Resource ID of the Log Analytics workspace.')
output logAnalyticsWorkspaceId string = logAnalytics.id

@description('Resource ID of the Application Insights component.')
output applicationInsightsId string = applicationInsights.id

@description('Name of the Application Insights component.')
output applicationInsightsName string = applicationInsights.name

@description('Connection string consumed by the OpenTelemetry → Azure Monitor exporter.')
output connectionString string = applicationInsights.properties.ConnectionString
