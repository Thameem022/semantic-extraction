@description('Principal ID (objectId) of the Function App managed identity')
param principalId string

@description('Storage account resource ID to scope the role assignment to')
param storageAccountId string

// Built-in role definition ID for "Storage Blob Data Contributor"
// https://learn.microsoft.com/azure/role-based-access-control/built-in-roles#storage
var storageBlobDataContributorRoleId = 'ba92f5b4-2d11-453d-a403-e96b0029c9fe'

// Role assignment granting the Function App access to blobs in the storage account
resource storageBlobDataContributor 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(storageAccountId, principalId, 'StorageBlobDataContributor')
  scope: resourceId('Microsoft.Storage/storageAccounts', split(storageAccountId, '/')[8])
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', storageBlobDataContributorRoleId)
    principalId: principalId
    principalType: 'ServicePrincipal'
  }
}

