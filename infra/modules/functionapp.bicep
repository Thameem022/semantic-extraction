// Function App module: Linux Consumption plan + Python 3.12 Function App (v4),
// system-assigned managed identity, app settings for blob trigger.

@description('Application base name. Used in resource naming.')
param appName string

@description('Deployment environment (e.g. dev, prod).')
param environment string

@description('Azure region for the Function App.')
param location string

@description('Common resource tags.')
param tags object = {}

@description('Resource ID of the storage account used for AzureWebJobsStorage.')
param storageAccountId string

@description('Name of the storage account used for AzureWebJobsStorage.')
param storageAccountName string

@description('Resource ID of the Log Analytics workspace.')
param logAnalyticsWorkspaceId string

@description('Application Insights connection string.')
param applicationInsightsConnectionString string

var hostingPlanName = '${appName}-${environment}-plan'
var functionAppName = '${appName}-${environment}-func'

resource storageAccount 'Microsoft.Storage/storageAccounts@2023-01-01' existing = {
  name: storageAccountName
}

var listKeysResult = listKeys(storageAccount.id, '2023-01-01')
var storageConnectionString = 'DefaultEndpointsProtocol=https;AccountName=${storageAccountName};AccountKey=${listKeysResult.keys[0].value};EndpointSuffix=core.windows.net'

resource hostingPlan 'Microsoft.Web/serverfarms@2023-01-01' = {
  name: hostingPlanName
  location: location
  kind: 'linux'
  tags: tags
  sku: {
    name: 'Y1'
    tier: 'Dynamic'
  }
  properties: {
    reserved: true
  }
}

resource functionApp 'Microsoft.Web/sites@2023-01-01' = {
  name: functionAppName
  location: location
  kind: 'functionapp,linux'
  tags: tags
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    serverFarmId: hostingPlan.id
    httpsOnly: true
    siteConfig: {
      linuxFxVersion: 'Python|3.12'
      appSettings: [
        { name: 'AzureWebJobsStorage', value: storageConnectionString }
        { name: 'WEBSITE_RUN_FROM_PACKAGE', value: '1' }
        { name: 'FUNCTIONS_EXTENSION_VERSION', value: '~4' }
        { name: 'FUNCTIONS_WORKER_RUNTIME', value: 'python' }
        { name: 'APPINSIGHTS_CONNECTIONSTRING', value: applicationInsightsConnectionString }
        { name: 'APPLICATIONINSIGHTS_CONNECTION_STRING', value: applicationInsightsConnectionString }
        { name: 'WEBSITE_CONTENTOVERVNET', value: '1' }
        { name: 'WEBSITE_CONTENTAZUREFILECONNECTIONSTRING', value: storageConnectionString }
      ]
    }
  }
}

resource functionDiagnostics 'Microsoft.Insights/diagnosticSettings@2021-05-01-preview' = {
  name: '${functionApp.name}-diag'
  scope: functionApp
  properties: {
    workspaceId: logAnalyticsWorkspaceId
    logs: [
      {
        category: 'FunctionAppLogs'
        enabled: true
        retentionPolicy: { enabled: false, days: 0 }
      }
    ]
    metrics: [
      {
        category: 'AllMetrics'
        enabled: true
        retentionPolicy: { enabled: false, days: 0 }
      }
    ]
  }
}

output functionAppName string = functionApp.name
output functionAppId string = functionApp.id
output functionAppPrincipalId string = functionApp.identity.principalId
