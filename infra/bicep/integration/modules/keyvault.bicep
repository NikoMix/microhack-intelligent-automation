@description('Azure region for the Key Vault.')
param location string

@description('Globally unique Key Vault name (3-24 chars).')
@minLength(3)
@maxLength(24)
param name string

@description('Principal ID of the managed identity granted Key Vault Secrets User.')
param readerPrincipalId string

@description('Enable purge protection. Recommended in prod; off in dev/test for easy lab reset.')
param enablePurgeProtection bool = false

@description('GitHub token (or provider key) stored as the github-token secret.')
@secure()
param gitHubToken string

@description('API key for the on-prem stub, stored as the onprem-api-key secret.')
@secure()
param onPremApiKey string

@description('Resource tags applied to the Key Vault.')
param tags object = {}

// Built-in role: Key Vault Secrets User (read secret values).
var keyVaultSecretsUserRoleId = '4633458b-17de-408a-b874-0445c86b69e6'

resource keyVault 'Microsoft.KeyVault/vaults@2024-11-01' = {
  name: name
  location: location
  tags: tags
  properties: {
    sku: {
      family: 'A'
      name: 'standard'
    }
    tenantId: subscription().tenantId
    enableRbacAuthorization: true
    enableSoftDelete: true
    softDeleteRetentionInDays: 7
    enablePurgeProtection: enablePurgeProtection ? true : null
    publicNetworkAccess: 'Enabled'
    networkAcls: {
      bypass: 'AzureServices'
      defaultAction: 'Allow'
    }
  }
}

resource gitHubTokenSecret 'Microsoft.KeyVault/vaults/secrets@2024-11-01' = {
  parent: keyVault
  name: 'github-token'
  properties: {
    value: gitHubToken
  }
}

resource onPremApiKeySecret 'Microsoft.KeyVault/vaults/secrets@2024-11-01' = {
  parent: keyVault
  name: 'onprem-api-key'
  properties: {
    value: onPremApiKey
  }
}

resource secretsUserAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(keyVault.id, readerPrincipalId, keyVaultSecretsUserRoleId)
  scope: keyVault
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', keyVaultSecretsUserRoleId)
    principalId: readerPrincipalId
    principalType: 'ServicePrincipal'
  }
}

@description('Key Vault resource name.')
output name string = keyVault.name

@description('Key Vault resource ID.')
output id string = keyVault.id

@description('Key Vault URI.')
output vaultUri string = keyVault.properties.vaultUri
