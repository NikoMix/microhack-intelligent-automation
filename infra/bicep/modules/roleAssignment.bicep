targetScope = 'resourceGroup'

@description('Microsoft Entra principal ID that receives the role assignment.')
param principalId string

@description('Built-in role definition GUID. Leave empty to use roleName.')
param roleDefinitionId string = ''

@description('Well-known built-in role name. Used when roleDefinitionId is empty.')
@allowed([
  'Key Vault Secrets User'
  'Storage Blob Data Contributor'
  'Cognitive Services OpenAI User'
  'Monitoring Metrics Publisher'
])
param roleName string = 'Key Vault Secrets User'

@description('Principal type for the role assignment.')
@allowed([
  'Device'
  'ForeignGroup'
  'Group'
  'ServicePrincipal'
  'User'
])
param principalType string = 'ServicePrincipal'

var wellKnownRoles = {
  'Key Vault Secrets User': '4633458b-17de-408a-b874-0445c86b69e6'
  'Storage Blob Data Contributor': 'ba92f5b4-2d11-453d-a403-e96b0029c9fe'
  'Cognitive Services OpenAI User': '5e0bd9bd-7b93-4f28-af87-19fc36ad61bd'
  'Monitoring Metrics Publisher': '3913510d-42f4-4e42-8a64-420c390055eb'
}
var selectedRoleDefinitionId = empty(roleDefinitionId) ? wellKnownRoles[roleName] : roleDefinitionId
var roleDefinitionResourceId = subscriptionResourceId('Microsoft.Authorization/roleDefinitions', selectedRoleDefinitionId)

resource assignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(resourceGroup().id, principalId, selectedRoleDefinitionId)
  properties: {
    roleDefinitionId: roleDefinitionResourceId
    principalId: principalId
    principalType: principalType
  }
}

@description('Azure resource ID of the created role assignment.')
output resourceId string = assignment.id

@description('Role definition resource ID used for the assignment.')
output roleDefinitionResourceId string = roleDefinitionResourceId

@description('Name of the role assignment resource.')
output name string = assignment.name
