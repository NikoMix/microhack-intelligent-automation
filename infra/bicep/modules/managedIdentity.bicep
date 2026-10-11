targetScope = 'resourceGroup'

@description('Name of the user-assigned managed identity.')
param name string

@description('Azure region for the managed identity.')
param location string = resourceGroup().location

@description('Tags applied to the managed identity.')
param tags object = {}

resource identity 'Microsoft.ManagedIdentity/userAssignedIdentities@2024-11-30' = {
  name: name
  location: location
  tags: union(tags, {
    module: 'managedIdentity'
  })
}

@description('Microsoft Entra principal ID of the managed identity.')
output principalId string = identity.properties.principalId

@description('Client ID of the managed identity for application configuration.')
output clientId string = identity.properties.clientId

@description('Azure resource ID of the managed identity.')
output resourceId string = identity.id

@description('Name of the managed identity.')
output name string = identity.name
