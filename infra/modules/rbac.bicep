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

var storageBlobDataContributorRoleId = 'ba92f5b4-2d11-453d-a403-e96b0029c9fe'
var roleAssignmentGuid = guid(appName, environment, storageAccountId, storageBlobDataContributorRoleId)

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
