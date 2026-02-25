@description('Environment name, e.g. dev or prod')
param environment string

@description('Name prefix for resources')
param namePrefix string

@description('Azure location for the storage account')
param location string

var storageApiVersion = '2023-01-01'

// Storage account name must be globally unique, 3-24 chars, alphanumeric and lowercase
var storageAccountName = toLower('${namePrefix}st${environment}${uniqueString(resourceGroup().id)}')

resource storageAccount 'Microsoft.Storage/storageAccounts@2023-01-01' = {
  name: storageAccountName
  location: location
  sku: {
    name: 'Standard_LRS'
  }
  kind: 'StorageV2'
  properties: {
    accessTier: 'Hot'
    supportsHttpsTrafficOnly: true
    allowBlobPublicAccess: false
    minimumTlsVersion: 'TLS1_2'
  }
}

resource blobService 'Microsoft.Storage/storageAccounts/blobServices@2023-01-01' = {
  name: '${storageAccount.name}/default'
  properties: {
    deleteRetentionPolicy: {
      enabled: true
      days: 7
    }
    containerDeleteRetentionPolicy: {
      enabled: true
      days: 7
    }
    isVersioningEnabled: true
  }
}

@description('Incoming blobs container')
resource incomingContainer 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-01-01' = {
  name: '${storageAccount.name}/${blobService.name}/incoming'
  properties: {}
}

@description('Raw blobs container')
resource rawContainer 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-01-01' = {
  name: '${storageAccount.name}/${blobService.name}/raw'
  properties: {}
}

@description('Duplicate blobs container')
resource duplicatesContainer 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-01-01' = {
  name: '${storageAccount.name}/${blobService.name}/duplicates'
  properties: {}
}

@description('Rejected blobs container')
resource rejectedContainer 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-01-01' = {
  name: '${storageAccount.name}/${blobService.name}/rejected'
  properties: {}
}

var storageAccountKey = listKeys(storageAccount.name, storageApiVersion).keys[0].value

@description('Name of the storage account')
output storageAccountName string = storageAccount.name

@description('Resource ID of the storage account')
output storageAccountId string = storageAccount.id

@description('Blob service endpoint URL')
output blobServiceEndpoint string = storageAccount.properties.primaryEndpoints.blob

@description('Connection string for the storage account (intended for dev use)')
output storageConnectionString string = 'DefaultEndpointsProtocol=https;AccountName=${storageAccount.name};AccountKey=${storageAccountKey};EndpointSuffix=${environment().suffixes.storage}'

