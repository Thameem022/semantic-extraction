// Azure AI Document Intelligence (formerly Form Recognizer) for OCR (prebuilt-layout).
// Used by the Function App fn_run_ocr.

@description('Application base name. Used in resource naming.')
param appName string

@description('Deployment environment (e.g. dev, prod).')
param environment string

@description('Azure region for the resource.')
param location string

@description('Common resource tags.')
param tags object = {}

@description('SKU for Document Intelligence. S0 is standard; F0 is free tier.')
param skuName string = 'S0'

@description('Set to true to restore a soft-deleted Document Intelligence account with the same name instead of creating new. Use once after a failed deploy due to FlagMustBeSetForRestore, then set back to false.')
param restoreSoftDeletedAccount bool = false

var prefix = toLower('${replace(appName, '-', '')}${replace(environment, '-', '')}di')
var accountName = '${prefix}${uniqueString(resourceGroup().id)}'

resource documentIntelligence 'Microsoft.CognitiveServices/accounts@2023-05-01' = {
  name: accountName
  location: location
  kind: 'FormRecognizer'
  tags: tags
  sku: {
    name: skuName
  }
  properties: {
    customSubDomainName: accountName
    publicNetworkAccess: 'Enabled'
    restore: restoreSoftDeletedAccount
  }
}

var endpoint = documentIntelligence.properties.endpoint
var primaryKey = documentIntelligence.listKeys().key1

output documentIntelligenceAccountName string = documentIntelligence.name
output documentIntelligenceEndpoint string = endpoint
@secure()
output documentIntelligencePrimaryKey string = primaryKey
