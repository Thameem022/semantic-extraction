@description('Environment name, e.g. dev or prod')
param environment string

@description('Name prefix for resources')
param namePrefix string

@description('Azure location for monitoring resources')
param location string

// Log Analytics Workspace
var lawName = toLower('${namePrefix}law${environment}${uniqueString(resourceGroup().id)}')

resource logAnalyticsWorkspace 'Microsoft.OperationalInsights/workspaces@2022-10-01' = {
  name: lawName
  location: location
  properties: {
    sku: {
      name: 'PerGB2018'
    }
    retentionInDays: 30
    publicNetworkAccessForIngestion: 'Enabled'
    publicNetworkAccessForQuery: 'Enabled'
  }
}

// Application Insights (workspace-based)
var appInsightsName = toLower('${namePrefix}ai${environment}${uniqueString(resourceGroup().id)}')

resource appInsights 'Microsoft.Insights/components@2020-02-02' = {
  name: appInsightsName
  location: location
  kind: 'web'
  properties: {
    Application_Type: 'web'
    Flow_Type: 'Bluefield'
    WorkspaceResourceId: logAnalyticsWorkspace.id
    IngestionMode: 'LogAnalytics'
  }
}

@description('Log Analytics workspace resource ID')
output workspaceId string = logAnalyticsWorkspace.id

@description('Application Insights name')
output appInsightsName string = appInsights.name

@description('Application Insights connection string')
output appInsightsConnectionString string = appInsights.properties.ConnectionString

