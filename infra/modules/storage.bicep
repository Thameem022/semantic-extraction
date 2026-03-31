// Storage module: creates a GPv2 storage account with blob versioning,
// soft delete (retentionDays) and required containers: incoming, raw, duplicates,
// rejected, ocr-raw, ocr-layout, candidates.

@description('Application base name. Used in resource naming.')
param appName string

@description('Deployment environment (e.g. dev, prod).')
param environment string

@description('Azure region for the storage account.')
param location string

@description('Retention in days for soft delete.')
param retentionDays int = 7

@description('Common resource tags.')
param tags object = {}

var prefix = toLower('${replace(appName, '-', '')}${replace(environment, '-', '')}sa')
var storageAccountName = '${prefix}${uniqueString(resourceGroup().id)}'

resource storageAccount 'Microsoft.Storage/storageAccounts@2023-01-01' = {
  name: storageAccountName
  location: location
  sku: {
    name: 'Standard_LRS'
  }
  kind: 'StorageV2'
  tags: tags
  properties: {
    accessTier: 'Hot'
    minimumTlsVersion: 'TLS1_2'
    allowBlobPublicAccess: false
    supportsHttpsTrafficOnly: true
    encryption: {
      services: {
        blob: {
          enabled: true
        }
        file: {
          enabled: true
        }
      }
      keySource: 'Microsoft.Storage'
    }
  }
}

// Blob service: soft delete and versioning
resource blobService 'Microsoft.Storage/storageAccounts/blobServices@2023-01-01' = {
  parent: storageAccount
  name: 'default'
  properties: {
    deleteRetentionPolicy: {
      enabled: true
      days: retentionDays
    }
    isVersioningEnabled: true
  }
}

resource containerIncoming 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-01-01' = {
  parent: blobService
  name: 'incoming'
  properties: {
    publicAccess: 'None'
  }
}

resource containerRaw 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-01-01' = {
  parent: blobService
  name: 'raw'
  properties: {
    publicAccess: 'None'
  }
}

resource containerDuplicates 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-01-01' = {
  parent: blobService
  name: 'duplicates'
  properties: {
    publicAccess: 'None'
  }
}

resource containerRejected 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-01-01' = {
  parent: blobService
  name: 'rejected'
  properties: {
    publicAccess: 'None'
  }
}

resource containerOcrRaw 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-01-01' = {
  parent: blobService
  name: 'ocr-raw'
  properties: {
    publicAccess: 'None'
  }
}

resource containerOcrLayout 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-01-01' = {
  parent: blobService
  name: 'ocr-layout'
  properties: {
    publicAccess: 'None'
  }
}

resource containerCandidates 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-01-01' = {
  parent: blobService
  name: 'candidates'
  properties: {
    publicAccess: 'None'
  }
}

var storageAccountKey = storageAccount.listKeys().keys[0].value
var storageConnectionString = 'DefaultEndpointsProtocol=https;AccountName=${storageAccount.name};AccountKey=${storageAccountKey};EndpointSuffix=core.windows.net'

output storageAccountName string = storageAccount.name
output storageAccountId string = storageAccount.id
output storageConnectionString string = storageConnectionString
