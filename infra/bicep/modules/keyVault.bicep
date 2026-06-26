targetScope = 'resourceGroup'

@description('Name of the Key Vault. Must be globally unique and no more than 24 characters.')
@minLength(3)
@maxLength(24)
param name string

@description('Azure region for the Key Vault.')
param location string = resourceGroup().location

@description('Tags applied to the Key Vault.')
param tags object = {}

@description('Tenant ID used by the Key Vault. Defaults to the deployment tenant.')
param tenantId string = tenant().tenantId

@description('Allow public network access for training labs that do not deploy private endpoints. Keep false for production.')
param allowPublicAccess bool = false

@description('Key Vault SKU family and name. Standard is the lowest-cost production SKU.')
@allowed([
  'standard'
  'premium'
])
param skuName string = 'standard'

@description('Optional Log Analytics workspace resource ID for Key Vault audit and metric diagnostic settings. Leave empty to skip diagnostics.')
param diagnosticWorkspaceId string = ''

resource vault 'Microsoft.KeyVault/vaults@2024-11-01' = {
  name: name
  location: location
  tags: union(tags, {
    module: 'keyVault'
  })
  properties: {
    tenantId: tenantId
    sku: {
      family: 'A'
      name: skuName
    }
    enableRbacAuthorization: true
    enabledForDeployment: false
    enabledForDiskEncryption: false
    enabledForTemplateDeployment: false
    enableSoftDelete: true
    softDeleteRetentionInDays: 90
    enablePurgeProtection: true
    publicNetworkAccess: allowPublicAccess ? 'Enabled' : 'Disabled'
    networkAcls: {
      bypass: 'AzureServices'
      defaultAction: allowPublicAccess ? 'Allow' : 'Deny'
    }
  }
}

#disable-next-line use-recent-api-versions // 2021-05-01-preview is the current diagnosticSettings extension API shape for category-based logs and metrics.
resource diagnostics 'Microsoft.Insights/diagnosticSettings@2021-05-01-preview' = if (!empty(diagnosticWorkspaceId)) {
  name: 'diag-${name}'
  scope: vault
  properties: {
    workspaceId: diagnosticWorkspaceId
    logs: [
      {
        category: 'AuditEvent'
        enabled: true
      }
    ]
    metrics: [
      {
        category: 'AllMetrics'
        enabled: true
      }
    ]
  }
}

@description('DNS URI of the Key Vault.')
output vaultUri string = vault.properties.vaultUri

@description('Name of the Key Vault.')
output name string = vault.name

@description('Azure resource ID of the Key Vault.')
output resourceId string = vault.id


