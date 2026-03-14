// Cosmos DB module: SQL API account, database and container for semantic-extraction.
// Supports serverless (default) or provisioned capacity mode.

@description('Application base name. Used in resource naming.')
param appName string

@description('Deployment environment (e.g. dev, prod).')
param environment string

@description('Azure region for the Cosmos DB account. Defaults to resource group location.')
param location string = resourceGroup().location

@description('Common resource tags.')
param tags object = {}

@description('Capacity mode: serverless (no RU/s) or provisioned (configurable throughput).')
@allowed([
  'serverless'
  'provisioned'
])
param cosmosCapacityMode string = 'serverless'

@description('Database throughput in RU/s. Only used when cosmosCapacityMode is provisioned.')
param databaseThroughput int = 400

@description('Database name.')
param cosmosDbName string = 'semex'

@description('Container name.')
param cosmosContainerName string = 'documents'

@description('Partition key path for the container.')
param partitionKeyPath string = '/policyType'

var isServerless = cosmosCapacityMode == 'serverless'
var prefix = toLower('${replace(appName, '-', '')}${replace(environment, '-', '')}cosmos')
var cosmosAccountName = '${prefix}${uniqueString(resourceGroup().id)}'

resource cosmosAccount 'Microsoft.DocumentDB/databaseAccounts@2023-04-15' = {
  name: cosmosAccountName
  location: location
  kind: 'GlobalDocumentDB'
  tags: tags
  properties: {
    databaseAccountOfferType: 'Standard'
    locations: [
      {
        locationName: location
        failoverPriority: 0
      }
    ]
    capabilities: isServerless ? [
      { name: 'EnableServerless' }
    ] : []
    consistencyPolicy: {
      defaultConsistencyLevel: 'Session'
    }
  }
}

resource sqlDatabase 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases@2023-04-15' = {
  parent: cosmosAccount
  name: cosmosDbName
  properties: {
    resource: {
      id: cosmosDbName
    }
    options: isServerless ? null : { throughput: databaseThroughput }
  }
}

resource sqlContainer 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2023-04-15' = {
  parent: sqlDatabase
  name: cosmosContainerName
  properties: {
    resource: {
      id: cosmosContainerName
      partitionKey: {
        paths: [partitionKeyPath]
        kind: 'Hash'
      }
      uniqueKeyPolicy: {
        uniqueKeys: [
          {
            paths: [
              '/sha256'
            ]
          }
        ]
      }
      indexingPolicy: {
        indexingMode: 'consistent'
        automatic: true
        includedPaths: [
          {
            path: '/*'
          }
          {
            path: '/status/?'
          }
          {
            path: '/uploadedAtUtc/?'
          }
          {
            path: '/policyType/?'
          }
        ]
      }
    }
  }
}

var cosmosEndpoint = cosmosAccount.properties.documentEndpoint
var cosmosPrimaryKey = cosmosAccount.listKeys().primaryMasterKey

output cosmosAccountName string = cosmosAccount.name
output cosmosDbName string = cosmosDbName
output cosmosContainerName string = cosmosContainerName
output cosmosEndpoint string = cosmosEndpoint
output cosmosPrimaryKey string = cosmosPrimaryKey
