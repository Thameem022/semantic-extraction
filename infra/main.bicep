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

@description('Retention in days for logs and soft delete.')
param retentionDays int = 7

@description('Common resource tags.')
param tags object = {}

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
    location: location
    tags: tags
    cosmosCapacityMode: cosmosCapacityMode
    databaseThroughput: cosmosDatabaseThroughput
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
