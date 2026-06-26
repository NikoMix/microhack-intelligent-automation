using './main.bicep'

// Sample parameters for Lab 3. Override namePrefix/location per learner or environment.
// All connections are identity-based; no secrets appear in this file.

param namePrefix = 'lab3doc'
param location = 'swedencentral'

// Flex Consumption sizing (free to scale to zero; pay only for active executions).
param instanceMemoryMB = 2048
param maximumInstanceCount = 100

// Document Intelligence default model used by the pipeline when a request omits one.
param documentIntelligenceSku = 'S0'

// Leave LLM post-processing off by default (GitHub Models / Azure OpenAI / Foundry
// can be enabled later by setting DocumentProcessing__EnableInsights=true plus the
// INFERENCE_PROVIDER settings on the Function App).
param enableInsights = false

param incomingDocumentsContainerName = 'incoming-documents'
param deploymentStorageContainerName = 'app-package'
param reviewQueueName = 'document-review'

param tags = {
  project: 'microhack-intelligent-automation'
  lab: 'lab-3-document-processing'
  module: 'B.1.1'
}
