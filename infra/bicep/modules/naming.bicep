targetScope = 'resourceGroup'

@description('Short workload identifier used as the base for every generated name. Use lowercase letters and numbers where possible.')
@minLength(2)
@maxLength(12)
param workloadName string

@description('Deployment environment suffix. Controls deterministic environment-specific naming.')
@allowed([
  'dev'
  'test'
  'prod'
])
param environment string

@description('Azure region for the deployment. The module converts common regions to compact abbreviations for shorter names.')
param location string = resourceGroup().location

@description('Optional numeric or short text instance discriminator for multiple lab deployments in the same resource group.')
@maxLength(4)
param instance string = '001'

var normalizedWorkload = toLower(replace(replace(replace(replace(workloadName, '-', ''), '_', ''), ' ', ''), '.', ''))
var normalizedEnvironment = toLower(environment)
var normalizedInstance = toLower(replace(replace(replace(replace(instance, '-', ''), '_', ''), ' ', ''), '.', ''))
var locationAbbreviations = {
  swedencentral: 'sec'
  westeurope: 'weu'
  northeurope: 'neu'
  eastus: 'eus'
  eastus2: 'eus2'
  westus: 'wus'
  westus2: 'wus2'
  centralus: 'cus'
  uksouth: 'uks'
  ukwest: 'ukw'
}
var normalizedLocation = toLower(replace(replace(location, ' ', ''), '-', ''))
var locationAbbr = locationAbbreviations[?normalizedLocation] ?? take(normalizedLocation, 5)
var compactPrefix = '${normalizedWorkload}${normalizedEnvironment}${locationAbbr}${normalizedInstance}'
var uniqueSuffixValue = toLower(uniqueString(resourceGroup().id))
var shortSuffix = take(uniqueSuffixValue, 6)
var resourcePrefixValue = '${normalizedWorkload}-${normalizedEnvironment}-${locationAbbr}-${normalizedInstance}'

@description('Hyphenated prefix suitable for resource names that allow hyphens.')
output resourcePrefix string = resourcePrefixValue

@description('Deterministic suffix derived from the resource group ID for collision-resistant names.')
output uniqueSuffix string = uniqueSuffixValue

@description('Consistent resource names for the shared platform foundation modules.')
output names object = {
  logAnalytics: take('law-${resourcePrefixValue}-${shortSuffix}', 63)
  appInsights: take('appi-${resourcePrefixValue}-${shortSuffix}', 255)
  managedIdentity: take('id-${resourcePrefixValue}-${shortSuffix}', 128)
  keyVault: take('kv-${compactPrefix}-${shortSuffix}', 24)
  storageAccount: take('st${compactPrefix}${take(uniqueSuffixValue, 8)}', 24)
}

