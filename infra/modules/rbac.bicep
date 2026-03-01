// RBAC module: assigns "Storage Blob Data Contributor" to Function App managed identity
// at storage account scope. Uses deterministic GUID for role assignment name.

@description('Application base name. Used in resource naming.')
param appName string

@description('Deployment environment (e.g. dev, prod).')
param environment string

@description('Resource ID of the storage account to scope the role assignment.')
param storageAccountId string

@description('Name of the storage account (for existing reference).')
param storageAccountName string

@description('Principal ID of the Function App managed identity.')
param principalId string

@description('Name of the Cosmos DB account.')
param cosmosAccountName string

var storageBlobDataContributorRoleId = 'ba92f5b4-2d11-453d-a403-e96b0029c9fe'
var roleAssignmentGuid = guid(appName, environment, storageAccountId, storageBlobDataContributorRoleId)

var cosmosDbBuiltInDataContributorRoleId = '00000000-0000-0000-0000-000000000002'
var cosmosRoleAssignmentGuid = guid(appName, environment, cosmosAccountName, cosmosDbBuiltInDataContributorRoleId)

resource storageAccount 'Microsoft.Storage/storageAccounts@2023-01-01' existing = {
  name: storageAccountName
}

resource storageBlobContributorAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: storageAccount
  name: roleAssignmentGuid
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', storageBlobDataContributorRoleId)
    principalId: principalId
    principalType: 'ServicePrincipal'
  }
}

resource cosmosAccount 'Microsoft.DocumentDB/databaseAccounts@2023-04-15' existing = {
  name: cosmosAccountName
}

resource cosmosDbDataContributorRole 'Microsoft.DocumentDB/databaseAccounts/sqlRoleDefinitions@2024-08-15' existing = {
  parent: cosmosAccount
  name: cosmosDbBuiltInDataContributorRoleId
}

resource cosmosDbDataContributorAssignment 'Microsoft.DocumentDB/databaseAccounts/sqlRoleAssignments@2024-08-15' = {
  parent: cosmosAccount
  name: cosmosRoleAssignmentGuid
  properties: {
    roleDefinitionId: cosmosDbDataContributorRole.id
    principalId: principalId
    scope: cosmosAccount.id
  }
}
