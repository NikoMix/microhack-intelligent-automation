// Azure AI Search service — the RAG retrieval backend the agent queries when
// RETRIEVER_BACKEND=azure_search. Defaults to the inexpensive 'basic' tier; 'free' is allowed
// for zero-cost labs (one free service per subscription; no semantic ranker).
metadata description = 'Azure AI Search service for RAG retrieval.'

@description('Azure region for the search service.')
param location string

@description('Name of the search service (3-60 lowercase letters, digits, dashes).')
param name string

@description('Tags applied to the search service.')
param tags object = {}

@description('Pricing tier. free = zero cost (1 per subscription, no semantic). basic = lab default.')
@allowed([
  'free'
  'basic'
  'standard'
  'standard2'
  'standard3'
])
param sku string = 'basic'

@description('Number of replicas (query throughput / availability).')
@minValue(1)
@maxValue(12)
param replicaCount int = 1

@description('Number of partitions (index size / scale).')
@allowed([
  1
  2
  3
  4
  6
  12
])
param partitionCount int = 1

@description('Semantic ranker plan. Requires basic tier or higher; leave disabled on the free tier.')
@allowed([
  'disabled'
  'free'
  'standard'
])
param semanticSearch string = 'disabled'

@description('Disable API-key (local) auth and require Entra ID RBAC only. Recommended outside the classroom.')
param disableLocalAuth bool = false

resource search 'Microsoft.Search/searchServices@2025-05-01' = {
  name: name
  location: location
  tags: tags
  sku: {
    name: sku
  }
  properties: {
    replicaCount: replicaCount
    partitionCount: partitionCount
    hostingMode: 'Default'
    publicNetworkAccess: 'enabled'
    semanticSearch: semanticSearch
    disableLocalAuth: disableLocalAuth
    // authOptions is mutually exclusive with disableLocalAuth: when keys stay enabled we allow
    // BOTH Entra ID RBAC and admin/query keys (aadOrApiKey) so the lab can demonstrate either.
    authOptions: disableLocalAuth
      ? null
      : {
          aadOrApiKey: {
            aadAuthFailureMode: 'http403'
          }
        }
  }
}

@description('Resource ID of the search service.')
output id string = search.id

@description('Name of the search service.')
output name string = search.name

@description('Search endpoint — set as AZURE_SEARCH_ENDPOINT.')
output endpoint string = 'https://${search.name}.search.windows.net'
