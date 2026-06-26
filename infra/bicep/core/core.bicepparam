using 'core.bicep'

param workloadName = 'iauto'
param environment = 'dev'
param location = 'swedencentral'
param instance = '001'
param tags = {
  purpose: 'training-lab'
  owner: 'microhack'
}
param deployKeyVault = true
param keyVaultAllowPublicAccess = false
param logAnalyticsDailyQuotaGb = '0.5'
