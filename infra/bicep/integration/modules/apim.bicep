@description('Azure region for API Management.')
param location string

@description('Globally unique API Management service name.')
param name string

@description('Publisher email (required by API Management).')
param publisherEmail string

@description('Publisher organisation name.')
param publisherName string

@description('Default host name of the Logic App the gateway fronts.')
param logicAppDefaultHostName string

@description('Name of the Logic App workflow exposed through the gateway.')
param workflowName string = 'enrich-order'

@description('Name of the workflow Request trigger invoked by the gateway.')
param triggerName string = 'When_an_order_status_request_is_received'

@description('Resource tags.')
param tags object = {}

var backendId = 'logicapp-backend'
var backendUrl = 'https://${logicAppDefaultHostName}/api/${workflowName}/triggers/${triggerName}/invoke'

// Consumption tier: capacity MUST be 0. This is the free/low-cost front door for the lab;
// the Developer tier (with VNet + portal) is documented as the paid upgrade path.
resource apim 'Microsoft.ApiManagement/service@2024-05-01' = {
  name: name
  location: location
  tags: tags
  sku: {
    name: 'Consumption'
    capacity: 0
  }
  properties: {
    publisherEmail: publisherEmail
    publisherName: publisherName
  }
}

resource backend 'Microsoft.ApiManagement/service/backends@2024-05-01' = {
  parent: apim
  name: backendId
  properties: {
    protocol: 'http'
    url: backendUrl
    title: 'Logic App Standard - enrich-order workflow'
  }
}

resource api 'Microsoft.ApiManagement/service/apis@2024-05-01' = {
  parent: apim
  name: 'orders'
  properties: {
    displayName: 'Orders'
    path: 'orders'
    protocols: [
      'https'
    ]
    subscriptionRequired: true
    serviceUrl: backendUrl
  }
}

resource enrichOperation 'Microsoft.ApiManagement/service/apis/operations@2024-05-01' = {
  parent: api
  name: 'enrich-order'
  properties: {
    displayName: 'Enrich order status'
    method: 'POST'
    urlTemplate: '/enrich'
    description: 'Routes an order-status request to the Logic App, which calls the Connector function.'
  }
}

// Policy name MUST be 'policy'. The gateway forwards to the Logic App backend. The workflow
// callback signature (sig/sv/sp query params) is supplied at runtime via a Key Vault-backed
// named value the trainer adds after the workflow is deployed (see the lab guide).
resource apiPolicy 'Microsoft.ApiManagement/service/apis/policies@2024-05-01' = {
  parent: api
  name: 'policy'
  properties: {
    format: 'xml'
    value: '''
<policies>
  <inbound>
    <base />
    <set-backend-service backend-id="logicapp-backend" />
  </inbound>
  <backend>
    <base />
  </backend>
  <outbound>
    <base />
  </outbound>
  <on-error>
    <base />
  </on-error>
</policies>
'''
  }
  dependsOn: [
    backend
    enrichOperation
  ]
}

@description('API Management gateway URL.')
output gatewayUrl string = apim.properties.gatewayUrl

@description('API Management service name.')
output name string = apim.name
