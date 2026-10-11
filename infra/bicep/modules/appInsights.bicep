targetScope = 'resourceGroup'

@description('Name of the workspace-based Application Insights component.')
param name string

@description('Azure region for the Application Insights component.')
param location string = resourceGroup().location

@description('Resource ID of the linked Log Analytics workspace.')
param logAnalyticsWorkspaceId string

@description('Tags applied to the Application Insights component.')
param tags object = {}

resource appInsights 'Microsoft.Insights/components@2020-02-02' = {
  name: name
  location: location
  kind: 'web'
  tags: union(tags, {
    module: 'appInsights'
  })
  properties: {
    Application_Type: 'web'
    WorkspaceResourceId: logAnalyticsWorkspaceId
    IngestionMode: 'LogAnalytics'
    publicNetworkAccessForIngestion: 'Enabled'
    publicNetworkAccessForQuery: 'Enabled'
  }
}

@description('Application Insights connection string for OpenTelemetry exporters and Azure SDK telemetry.')
output connectionString string = appInsights.properties.ConnectionString

@description('Application Insights instrumentation key for legacy SDK compatibility.')
output instrumentationKey string = appInsights.properties.InstrumentationKey

@description('Name of the Application Insights component.')
output name string = appInsights.name
