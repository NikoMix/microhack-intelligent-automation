// Least-privilege RBAC for the agent identity (and an optional developer/operator principal).
// The agent identity gets exactly what the runtime needs: query the index, call the model,
// publish telemetry. The optional developer principal gets index-authoring rights for the lab.
metadata description = 'RBAC role assignments for the agent identity and an optional developer principal.'

@description('Name of the Azure AI Search service.')
param searchName string

@description('Name of the Azure OpenAI / Foundry account.')
param openAiName string

@description('Name of the Application Insights component.')
param applicationInsightsName string

@description('Principal (object) ID of the user-assigned managed identity used by the agent runtime.')
param agentPrincipalId string

@description('Optional object ID of a developer/operator principal for index loading and local runs.')
param developerPrincipalId string = ''

@description('Principal type of the developer principal.')
@allowed([
  'User'
  'Group'
  'ServicePrincipal'
])
param developerPrincipalType string = 'User'

// Built-in role definition IDs (stable GUIDs).
var roleIds = {
  cognitiveServicesOpenAiUser: '5e0bd9bd-7b93-4f28-af87-19fc36ad61bd'
  searchIndexDataReader: '1407120a-92aa-4202-b7e9-c0e197c71c8f'
  searchIndexDataContributor: '8ebe5a00-799e-43f5-93ac-243d3dce84a7'
  searchServiceContributor: '7ca78c08-252a-4471-8644-bb5ff32d4ba0'
  monitoringMetricsPublisher: '3913510d-42f4-4e42-8a64-420c390055eb'
}

var hasDeveloper = !empty(developerPrincipalId)

resource search 'Microsoft.Search/searchServices@2025-05-01' existing = {
  name: searchName
}

resource openAi 'Microsoft.CognitiveServices/accounts@2024-10-01' existing = {
  name: openAiName
}

resource applicationInsights 'Microsoft.Insights/components@2020-02-02' existing = {
  name: applicationInsightsName
}

// --- Agent identity: query the index, call the model, publish telemetry ---

resource agentSearchReader 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(search.id, agentPrincipalId, roleIds.searchIndexDataReader)
  scope: search
  properties: {
    principalId: agentPrincipalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: subscriptionResourceId(
      'Microsoft.Authorization/roleDefinitions',
      roleIds.searchIndexDataReader
    )
  }
}

resource agentOpenAiUser 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(openAi.id, agentPrincipalId, roleIds.cognitiveServicesOpenAiUser)
  scope: openAi
  properties: {
    principalId: agentPrincipalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: subscriptionResourceId(
      'Microsoft.Authorization/roleDefinitions',
      roleIds.cognitiveServicesOpenAiUser
    )
  }
}

resource agentMetricsPublisher 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(applicationInsights.id, agentPrincipalId, roleIds.monitoringMetricsPublisher)
  scope: applicationInsights
  properties: {
    principalId: agentPrincipalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: subscriptionResourceId(
      'Microsoft.Authorization/roleDefinitions',
      roleIds.monitoringMetricsPublisher
    )
  }
}

// --- Optional developer principal: author/load the index and run locally with own identity ---

resource devSearchContributor 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (hasDeveloper) {
  name: guid(search.id, developerPrincipalId, roleIds.searchIndexDataContributor)
  scope: search
  properties: {
    principalId: developerPrincipalId
    principalType: developerPrincipalType
    roleDefinitionId: subscriptionResourceId(
      'Microsoft.Authorization/roleDefinitions',
      roleIds.searchIndexDataContributor
    )
  }
}

resource devSearchServiceContributor 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (hasDeveloper) {
  name: guid(search.id, developerPrincipalId, roleIds.searchServiceContributor)
  scope: search
  properties: {
    principalId: developerPrincipalId
    principalType: developerPrincipalType
    roleDefinitionId: subscriptionResourceId(
      'Microsoft.Authorization/roleDefinitions',
      roleIds.searchServiceContributor
    )
  }
}

resource devOpenAiUser 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (hasDeveloper) {
  name: guid(openAi.id, developerPrincipalId, roleIds.cognitiveServicesOpenAiUser)
  scope: openAi
  properties: {
    principalId: developerPrincipalId
    principalType: developerPrincipalType
    roleDefinitionId: subscriptionResourceId(
      'Microsoft.Authorization/roleDefinitions',
      roleIds.cognitiveServicesOpenAiUser
    )
  }
}
