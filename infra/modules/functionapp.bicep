@description('Environment name, e.g. dev or prod')
param environment string

@description('Name prefix for resources')
param namePrefix string

@description('Azure location for the Function App')
param location string

@description('Storage connection string for the Function App (dev-ok)')
param storageConnectionString string

@description('Application Insights connection string')
param appInsightsConnectionString string

// Hosting plan (Linux Consumption)
var planName = toLower('${namePrefix}plan${environment}${uniqueString(resourceGroup().id)}')

resource hostingPlan 'Microsoft.Web/serverfarms@2022-09-01' = {
  name: planName
  location: location
  sku: {
    name: 'Y1'
    tier: 'Dynamic'
  }
  kind: 'functionapp'
  properties: {
    reserved: true
  }
}

// Function App (Linux, Python 3.12) with system-assigned managed identity
var functionAppName = toLower('${namePrefix}fa${environment}${uniqueString(resourceGroup().id)}')

resource functionApp 'Microsoft.Web/sites@2022-09-01' = {
  name: functionAppName
  location: location
  kind: 'functionapp,linux'
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    serverFarmId: hostingPlan.id
    httpsOnly: true
    siteConfig: {
      linuxFxVersion: 'Python|3.12'
      appSettings: [
        {
          name: 'FUNCTIONS_WORKER_RUNTIME'
          value: 'python'
        }
        {
          name: 'AzureWebJobsStorage'
          value: storageConnectionString
        }
        {
          name: 'APPLICATIONINSIGHTS_CONNECTION_STRING'
          value: appInsightsConnectionString
        }
        {
          name: 'WEBSITE_RUN_FROM_PACKAGE'
          value: '1'
        }
      ]
    }
  }
}

@description('Function App name')
output functionAppName string = functionApp.name

@description('Function App resource ID')
output functionAppId string = functionApp.id

@description('Function App principal ID (system-assigned managed identity)')
output principalId string = functionApp.identity.principalId

