// User-assigned managed identity for the agent runtime.
// Preferred over keys: the agent authenticates to Azure OpenAI/Foundry and AI Search through
// Entra ID (DefaultAzureCredential) using this identity when deployed on Azure compute.
metadata description = 'User-assigned managed identity used by the agent runtime for Entra ID auth.'

@description('Azure region for the identity.')
param location string

@description('Name of the user-assigned managed identity.')
param name string

@description('Tags applied to the identity.')
param tags object = {}

resource identity 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = {
  name: name
  location: location
  tags: tags
}

@description('Resource ID of the managed identity.')
output id string = identity.id

@description('Name of the managed identity.')
output name string = identity.name

@description('Entra ID object (principal) ID — used for role assignments.')
output principalId string = identity.properties.principalId

@description('Client ID — set as AZURE_CLIENT_ID so DefaultAzureCredential selects this identity.')
output clientId string = identity.properties.clientId
