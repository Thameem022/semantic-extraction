// Main Bicep orchestrating all modules for semantic-extraction infra.
// Assumes resource group is created outside of this deployment.

@description('Application base name. Used in resource naming.')
param appName string = 'semex'

@description('Deployment environment (e.g. dev, prod).')
@allowed([
  'dev'
  'prod'
])
param environment string

@description('Azure region for all resources.')
param location string

@description('Azure region for Document Intelligence (must be in your subscription allowed list and support Cognitive Services).')
@allowed([
  'southeastasia'
  'uaenorth'
  'koreacentral'
])
param documentIntelligenceLocation string = 'southeastasia'

@description('Set to true to restore a soft-deleted Document Intelligence account (use once after FlagMustBeSetForRestore, then set back to false).')
param documentIntelligenceRestoreSoftDeleted bool = false

@description('Retention in days for logs and soft delete.')
param retentionDays int = 7

@description('Common resource tags.')
param tags object = {}

@description('Azure region for Cosmos DB. Use a region with capacity if the main location has high demand (e.g. southeastasia).')
param cosmosLocation string = 'southeastasia'

@description('Cosmos DB capacity mode: serverless or provisioned. Default serverless.')
@allowed([
  'serverless'
  'provisioned'
])
param cosmosCapacityMode string = 'serverless'

@description('Cosmos DB database throughput (RU/s). Only used when cosmosCapacityMode is provisioned.')
param cosmosDatabaseThroughput int = 400

// Storage account + containers
module storage 'modules/storage.bicep' = {
  name: 'storageDeployment'
  params: {
    appName: appName
    environment: environment
    location: location
    retentionDays: retentionDays
    tags: tags
  }
}

// Monitoring: Log Analytics + App Insights
module monitoring 'modules/monitoring.bicep' = {
  name: 'monitoringDeployment'
  params: {
    appName: appName
    environment: environment
    location: location
    retentionDays: retentionDays
    tags: tags
  }
}

// Cosmos DB: SQL API account, database (semex), container (documents)
module cosmos 'modules/cosmos.bicep' = {
  name: 'cosmosDeployment'
  params: {
    appName: appName
    environment: environment
    location: cosmosLocation
    tags: tags
    cosmosCapacityMode: cosmosCapacityMode
    databaseThroughput: cosmosDatabaseThroughput
  }
}

// Azure AI Document Intelligence (OCR / prebuilt-layout)
module documentintelligence 'modules/documentintelligence.bicep' = {
  name: 'documentIntelligenceDeployment'
  params: {
    appName: appName
    environment: environment
    location: documentIntelligenceLocation
    tags: tags
    restoreSoftDeletedAccount: documentIntelligenceRestoreSoftDeleted
  }
}

// Function App + Consumption plan
module functionapp 'modules/functionapp.bicep' = {
  name: 'functionAppDeployment'
  params: {
    appName: appName
    environment: environment
    location: location
    tags: tags
    storageConnectionString: storage.outputs.storageConnectionString
    logAnalyticsWorkspaceId: monitoring.outputs.logAnalyticsWorkspaceId
    applicationInsightsConnectionString: monitoring.outputs.applicationInsightsConnectionString
    cosmosEndpoint: cosmos.outputs.cosmosEndpoint
    cosmosKey: cosmos.outputs.cosmosPrimaryKey
    cosmosDbName: cosmos.outputs.cosmosDbName
    cosmosContainerName: cosmos.outputs.cosmosContainerName
    documentIntelligenceEndpoint: documentintelligence.outputs.documentIntelligenceEndpoint
    documentIntelligenceApiKey: documentintelligence.outputs.documentIntelligencePrimaryKey
  }
}

// RBAC for Function App managed identity on storage
module rbac 'modules/rbac.bicep' = {
  name: 'rbacDeployment'
  params: {
    appName: appName
    environment: environment
    storageAccountId: storage.outputs.storageAccountId
    storageAccountName: storage.outputs.storageAccountName
    principalId: functionapp.outputs.functionAppPrincipalId
    cosmosAccountName: cosmos.outputs.cosmosAccountName
  }
}

@description('Name of the storage account.')
output storageAccountName string = storage.outputs.storageAccountName

@description('Resource ID of the storage account.')
output storageAccountId string = storage.outputs.storageAccountId

@description('Name of the Function App.')
output functionAppName string = functionapp.outputs.functionAppName

@description('Name of the Application Insights component.')
output applicationInsightsName string = monitoring.outputs.applicationInsightsName

@description('Name of the Log Analytics workspace.')
output logAnalyticsWorkspaceName string = monitoring.outputs.logAnalyticsWorkspaceName

@description('Name of the Cosmos DB account.')
output cosmosAccountName string = cosmos.outputs.cosmosAccountName

@description('Name of the Cosmos DB (database).')
output cosmosDbName string = cosmos.outputs.cosmosDbName

@description('Name of the Cosmos DB container.')
output cosmosContainerName string = cosmos.outputs.cosmosContainerName

@description('Name of the Azure AI Document Intelligence account.')
output documentIntelligenceAccountName string = documentintelligence.outputs.documentIntelligenceAccountName
