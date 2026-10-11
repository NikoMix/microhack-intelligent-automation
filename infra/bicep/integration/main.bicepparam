using 'main.bicep'

param workloadName = 'iauto'
param environment = 'dev'
param location = 'swedencentral'
param instance = '006'
param tags = {
  costCenter: 'training'
  owner: 'train-the-trainer'
}
param apimPublisherName = 'Intelligent Automation Trainers'
param apimPublisherEmail = 'trainers@example.com'
param allowPublicNetworkAccess = true
