@description('Deployment environment, e.g. dev or prod')
param environment string

@description('Azure location for all resources')
param location string

@description('Name prefix for resources')
param namePrefix string

// Storage module
module storage './modules/storage.bicep' = {
  name: 'storage-${environment}'
  params: {
    environment: environment
    namePrefix: namePrefix
    location: location
  }
}

// Monitoring module
module monitoring './modules/monitoring.bicep' = {
  name: 'monitoring-${environment}'
  params: {
    environment: environment
    namePrefix: namePrefix
    location: location
  }
}

// Function App module (depends on storage + monitoring)
module functionApp './modules/functionapp.bicep' = {
  name: 'functionapp-${environment}'
  params: {
    environment: environment
    namePrefix: namePrefix
    location: location
    storageConnectionString: storage.outputs.storageConnectionString
    appInsightsConnectionString: monitoring.outputs.appInsightsConnectionString
  }
}

// RBAC module (depends on Function App + Storage)
module rbac './modules/rbac.bicep' = {
  name: 'rbac-${environment}'
  params: {
    principalId: functionApp.outputs.principalId
    storageAccountId: storage.outputs.storageAccountId
  }
}

@description('Resource group name where resources are deployed')
output resourceGroupName string = resourceGroup().name

@description('Storage account name')
output storageAccountName string = storage.outputs.storageAccountName

@description('Function App name')
output functionAppName string = functionApp.outputs.functionAppName

@description('Application Insights name')
output appInsightsName string = monitoring.outputs.appInsightsName

