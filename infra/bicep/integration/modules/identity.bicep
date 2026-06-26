@description('Azure region for the user-assigned managed identity.')
param location string

@description('Name of the user-assigned managed identity.')
param name string

@description('Resource tags applied to the identity.')
param tags object = {}

resource uami 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = {
  name: name
  location: location
  tags: tags
}

@description('Resource ID of the managed identity.')
output id string = uami.id

@description('Principal (object) ID used for role assignments.')
output principalId string = uami.properties.principalId

@description('Client ID consumed by app settings for managed-identity auth.')
output clientId string = uami.properties.clientId

@description('Name of the managed identity.')
output name string = uami.name
