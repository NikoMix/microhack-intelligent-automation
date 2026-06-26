// Sample parameters for Lab 4. Copy and adjust as needed, then deploy with:
//   az deployment group create -g <rg> -f main.bicep -p main.bicepparam
using './main.bicep'

param namePrefix = 'lab4kb'

// Pick a region where your chosen chat model + SKU is available (gpt-4o-mini GlobalStandard is
// broadly available in, e.g., swedencentral, eastus2, westus3).
param location = 'swedencentral'

// Search: 'basic' is the lab default. Switch to 'free' for zero cost (1 free service per
// subscription, no semantic ranker) or 'standard' for production scale + semantic 'standard'.
param searchSku = 'basic'
param searchSemanticSearch = 'disabled'
param searchIndexName = 'knowledge-index'

// Chat model deployment.
param openAiKind = 'AIServices'
param chatDeploymentName = 'gpt-4o-mini'
param chatModelName = 'gpt-4o-mini'
param chatModelVersion = '2024-07-18'
param chatDeploymentSku = 'GlobalStandard'
param chatCapacity = 8
param deployEmbedding = true

// Security: keep keys enabled for the classroom (Entra ID RBAC is always also granted).
// Set to true to require Entra ID only.
param disableLocalAuth = false

// Grant yourself index-authoring + model rights for hands-on loading and local runs:
//   az ad signed-in-user show --query id -o tsv
// param developerPrincipalId = '00000000-0000-0000-0000-000000000000'
// param developerPrincipalType = 'User'
