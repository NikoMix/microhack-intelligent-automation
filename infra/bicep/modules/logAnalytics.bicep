targetScope = 'resourceGroup'

@description('Name of the Log Analytics workspace.')
param name string

@description('Azure region for the Log Analytics workspace.')
param location string = resourceGroup().location

@description('Tags applied to the Log Analytics workspace.')
param tags object = {}

@description('Workspace retention in days. Thirty days keeps lab cost and data exposure low.')
@minValue(30)
@maxValue(730)
param retentionInDays int = 30

@description('Daily ingestion cap in GB as a JSON number string to allow fractional lab caps such as 0.5. Set to -1 to disable the cap when appropriate.')
param dailyQuotaGb string = '0.5'

resource workspace 'Microsoft.OperationalInsights/workspaces@2025-02-01' = {
  name: name
  location: location
  tags: union(tags, {
    module: 'logAnalytics'
  })
  properties: {
    sku: {
      name: 'PerGB2018'
    }
    retentionInDays: retentionInDays
    workspaceCapping: {
      dailyQuotaGb: json(dailyQuotaGb)
    }
    publicNetworkAccessForIngestion: 'Enabled'
    publicNetworkAccessForQuery: 'Enabled'
  }
}

@description('Azure resource ID of the Log Analytics workspace.')
output workspaceId string = workspace.id

@description('Log Analytics customer ID, also known as the workspace ID GUID.')
output customerId string = workspace.properties.customerId

@description('Name of the Log Analytics workspace.')
output name string = workspace.name
