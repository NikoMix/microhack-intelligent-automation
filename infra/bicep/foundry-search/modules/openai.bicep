// Azure AI Foundry / Azure OpenAI account (kind = AIServices by default).
// One account serves BOTH the `azure_openai` and `foundry` inference providers of the shared
// modular-inference layer — selection stays a configuration change, never a code change.
metadata description = 'Azure AI Foundry / Azure OpenAI account with a chat (and optional embedding) deployment.'

@description('Azure region for the account.')
param location string

@description('Name of the account; also used as the custom subdomain (DNS label) for token auth.')
param name string

@description('Tags applied to the account.')
param tags object = {}

@description('Account kind. AIServices is the unified Foundry resource; OpenAI is Azure OpenAI only.')
@allowed([
  'AIServices'
  'OpenAI'
])
param accountKind string = 'AIServices'

@description('Account pricing tier. S0 is standard pay-as-you-go.')
param skuName string = 'S0'

@description('Disable API-key auth and require Entra ID RBAC only. Recommended outside the classroom.')
param disableLocalAuth bool = false

@description('Name of the chat model deployment (also the AZURE_OPENAI_DEPLOYMENT / AZURE_AI_FOUNDRY_MODEL value).')
param chatDeploymentName string

@description('Chat model name, e.g. gpt-4o-mini.')
param chatModelName string

@description('Chat model version, e.g. 2024-07-18.')
param chatModelVersion string

@description('Deployment SKU. GlobalStandard offers the widest model/region availability.')
@allowed([
  'Standard'
  'GlobalStandard'
  'DataZoneStandard'
])
param chatDeploymentSku string = 'GlobalStandard'

@description('Chat deployment capacity in thousands of tokens-per-minute (TPM).')
@minValue(1)
param chatCapacity int = 8

@description('Also deploy a text-embedding model for the vector-search upgrade.')
param deployEmbedding bool = true

@description('Name of the embedding deployment.')
param embeddingDeploymentName string = 'text-embedding-3-small'

@description('Embedding model name.')
param embeddingModelName string = 'text-embedding-3-small'

@description('Embedding model version.')
param embeddingModelVersion string = '1'

@description('Embedding deployment capacity (thousands of TPM).')
@minValue(1)
param embeddingCapacity int = 8

resource account 'Microsoft.CognitiveServices/accounts@2024-10-01' = {
  name: name
  location: location
  tags: tags
  kind: accountKind
  sku: {
    name: skuName
  }
  properties: {
    customSubDomainName: name
    publicNetworkAccess: 'Enabled'
    disableLocalAuth: disableLocalAuth
    networkAcls: {
      defaultAction: 'Allow'
    }
  }
}

resource chat 'Microsoft.CognitiveServices/accounts/deployments@2024-10-01' = {
  parent: account
  name: chatDeploymentName
  sku: {
    name: chatDeploymentSku
    capacity: chatCapacity
  }
  properties: {
    model: {
      format: 'OpenAI'
      name: chatModelName
      version: chatModelVersion
    }
    versionUpgradeOption: 'OnceNewDefaultVersionAvailable'
  }
}

// Deployments on a single account must be created serially, so the embedding deployment
// depends on the chat deployment.
resource embedding 'Microsoft.CognitiveServices/accounts/deployments@2024-10-01' = if (deployEmbedding) {
  parent: account
  name: embeddingDeploymentName
  sku: {
    name: 'Standard'
    capacity: embeddingCapacity
  }
  properties: {
    model: {
      format: 'OpenAI'
      name: embeddingModelName
      version: embeddingModelVersion
    }
  }
  dependsOn: [
    chat
  ]
}

@description('Resource ID of the account.')
output id string = account.id

@description('Name of the account.')
output name string = account.name

@description('Azure OpenAI endpoint — set as AZURE_OPENAI_ENDPOINT.')
output openAiEndpoint string = 'https://${account.name}.openai.azure.com/'

@description('AI Services / Foundry endpoint — set as AZURE_AI_FOUNDRY_ENDPOINT.')
output aiServicesEndpoint string = account.properties.endpoint

@description('Name of the chat deployment.')
output chatDeploymentName string = chat.name

@description('Name of the embedding deployment (empty when not deployed).')
output embeddingDeploymentName string = deployEmbedding ? embeddingDeploymentName : ''
