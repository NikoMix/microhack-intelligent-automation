// =============================================================================================
// Lab 4 — Copilot Studio → Azure AI Foundry agent + RAG
// Provisions the Azure footprint for the grounded knowledge agent:
//   • Azure AI Search          — RAG retrieval backend (RETRIEVER_BACKEND=azure_search)
//   • Azure AI Foundry/OpenAI  — chat (+ optional embedding) model, serves azure_openai + foundry
//   • Application Insights      — OpenTelemetry → Azure Monitor sink
//   • User-assigned identity    — Entra ID auth for the agent runtime (no keys)
//   • RBAC                      — least-privilege role assignments
// Outputs are named to match the agent's environment-variable contract for copy/paste into .env.
// =============================================================================================
metadata description = 'Lab 4 Azure footprint: AI Search + Azure OpenAI/Foundry + App Insights + managed identity + RBAC.'

targetScope = 'resourceGroup'

@description('Azure region. Defaults to the resource group location.')
param location string = resourceGroup().location

@description('Short, lowercase prefix used to name resources.')
@minLength(2)
@maxLength(12)
param namePrefix string = 'lab4kb'

@description('Tags applied to every resource.')
param tags object = {
  workload: 'lab4-foundry-agent'
  course: 'module-b-intelligent-automation'
}

// --- Azure AI Search ---
@description('Search pricing tier. free = zero cost (1 per subscription); basic = lab default.')
@allowed([
  'free'
  'basic'
  'standard'
])
param searchSku string = 'basic'

@description('Semantic ranker plan (requires basic+; keep disabled on the free tier).')
@allowed([
  'disabled'
  'free'
  'standard'
])
param searchSemanticSearch string = 'disabled'

@description('Name of the search index the agent queries.')
param searchIndexName string = 'knowledge-index'

// --- Azure OpenAI / Foundry ---
@description('Account kind. AIServices is the unified Foundry resource; OpenAI is Azure OpenAI only.')
@allowed([
  'AIServices'
  'OpenAI'
])
param openAiKind string = 'AIServices'

@description('Chat model deployment name (AZURE_OPENAI_DEPLOYMENT / AZURE_AI_FOUNDRY_MODEL).')
param chatDeploymentName string = 'gpt-4o-mini'

@description('Chat model name.')
param chatModelName string = 'gpt-4o-mini'

@description('Chat model version.')
param chatModelVersion string = '2024-07-18'

@description('Chat deployment SKU.')
@allowed([
  'Standard'
  'GlobalStandard'
  'DataZoneStandard'
])
param chatDeploymentSku string = 'GlobalStandard'

@description('Chat deployment capacity (thousands of TPM). Keep small for the lab.')
@minValue(1)
param chatCapacity int = 8

@description('Also deploy a text-embedding model for the vector-search upgrade.')
param deployEmbedding bool = true

// --- Security ---
@description('Disable API-key auth on Search and Azure OpenAI and require Entra ID RBAC only.')
param disableLocalAuth bool = false

@description('Optional object ID of a developer/operator principal to grant index-authoring + model rights.')
param developerPrincipalId string = ''

@description('Principal type of the developer principal.')
@allowed([
  'User'
  'Group'
  'ServicePrincipal'
])
param developerPrincipalType string = 'User'

// --- Names ---
var resourceToken = toLower(uniqueString(subscription().id, resourceGroup().id, namePrefix))

module monitoring 'modules/monitoring.bicep' = {
  name: 'monitoring'
  params: {
    location: location
    tags: tags
    logAnalyticsName: '${namePrefix}-logs-${resourceToken}'
    applicationInsightsName: '${namePrefix}-appi-${resourceToken}'
  }
}

module identity 'modules/identity.bicep' = {
  name: 'identity'
  params: {
    location: location
    tags: tags
    name: '${namePrefix}-agent-id-${resourceToken}'
  }
}

module search 'modules/search.bicep' = {
  name: 'search'
  params: {
    location: location
    tags: tags
    name: '${namePrefix}-search-${resourceToken}'
    sku: searchSku
    semanticSearch: searchSemanticSearch
    disableLocalAuth: disableLocalAuth
  }
}

module openAi 'modules/openai.bicep' = {
  name: 'openai'
  params: {
    location: location
    tags: tags
    name: '${namePrefix}-aoai-${resourceToken}'
    accountKind: openAiKind
    disableLocalAuth: disableLocalAuth
    chatDeploymentName: chatDeploymentName
    chatModelName: chatModelName
    chatModelVersion: chatModelVersion
    chatDeploymentSku: chatDeploymentSku
    chatCapacity: chatCapacity
    deployEmbedding: deployEmbedding
  }
}

module roles 'modules/roles.bicep' = {
  name: 'roleAssignments'
  params: {
    searchName: search.outputs.name
    openAiName: openAi.outputs.name
    applicationInsightsName: monitoring.outputs.applicationInsightsName
    agentPrincipalId: identity.outputs.principalId
    developerPrincipalId: developerPrincipalId
    developerPrincipalType: developerPrincipalType
  }
}

// --- Outputs: copy these into your .env (names match the agent's environment contract) ---

@description('Set RETRIEVER_BACKEND to switch the agent from the local index to Azure AI Search.')
output RETRIEVER_BACKEND string = 'azure_search'

@description('AZURE_SEARCH_ENDPOINT')
output AZURE_SEARCH_ENDPOINT string = search.outputs.endpoint

@description('AZURE_SEARCH_INDEX')
output AZURE_SEARCH_INDEX string = searchIndexName

@description('AZURE_OPENAI_ENDPOINT (use with INFERENCE_PROVIDER=azure_openai)')
output AZURE_OPENAI_ENDPOINT string = openAi.outputs.openAiEndpoint

@description('AZURE_OPENAI_DEPLOYMENT')
output AZURE_OPENAI_DEPLOYMENT string = openAi.outputs.chatDeploymentName

@description('AZURE_AI_FOUNDRY_ENDPOINT (use with INFERENCE_PROVIDER=foundry)')
output AZURE_AI_FOUNDRY_ENDPOINT string = openAi.outputs.aiServicesEndpoint

@description('AZURE_AI_FOUNDRY_MODEL')
output AZURE_AI_FOUNDRY_MODEL string = openAi.outputs.chatDeploymentName

@description('APPLICATIONINSIGHTS_CONNECTION_STRING (sensitive — keep out of source control)')
output APPLICATIONINSIGHTS_CONNECTION_STRING string = monitoring.outputs.connectionString

@description('AZURE_CLIENT_ID — set so DefaultAzureCredential selects the agent identity on Azure compute.')
output AZURE_CLIENT_ID string = identity.outputs.clientId

@description('Resource ID of the agent identity (attach to the App Service / Container App / VM).')
output agentIdentityResourceId string = identity.outputs.id
