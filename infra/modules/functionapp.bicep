// Function App module: Linux plan + Python 3.12 Function App (v4).
// Uses Basic B1 by default (Consumption Y1 requires "Dynamic VMs" quota in the subscription).

@description('Application base name. Used in resource naming.')
param appName string

@description('Deployment environment (e.g. dev, prod).')
param environment string

@description('Azure region for the Function App.')
param location string

@description('Common resource tags.')
param tags object = {}

@description('Storage connection string for AzureWebJobsStorage (from storage module output).')
param storageConnectionString string

@description('Resource ID of the Log Analytics workspace.')
param logAnalyticsWorkspaceId string

@description('Application Insights connection string.')
param applicationInsightsConnectionString string

@description('Cosmos DB endpoint URL.')
param cosmosEndpoint string

@description('Cosmos DB primary key (will move to Key Vault later).')
param cosmosKey string

@description('Cosmos DB database name.')
param cosmosDbName string

@description('Cosmos DB container name.')
param cosmosContainerName string

@description('Azure AI Document Intelligence endpoint (e.g. https://<name>.cognitiveservices.azure.com).')
param documentIntelligenceEndpoint string

@description('Azure AI Document Intelligence API key.')
@secure()
param documentIntelligenceApiKey string

@description('Azure OpenAI HTTPS endpoint (Cognitive Services OpenAI account).')
param azureOpenAiEndpoint string

@description('Azure OpenAI API key (primary). Prefer Key Vault reference in production.')
@secure()
param azureOpenAiApiKey string

@description('Azure OpenAI chat deployment name (must match a deployment on the account).')
param azureOpenAiDeploymentName string

@description('Azure OpenAI API version for REST client.')
param azureOpenAiApiVersion string = '2024-08-01-preview'

@description('App Service Plan SKU: B1 (Basic) works without Consumption quota; use Y1 for Consumption when quota is available.')
param hostingPlanSku string = 'B1'

@description('App Service Plan tier: Basic for B1, Dynamic for Y1 Consumption.')
param hostingPlanTier string = 'Basic'

var hostingPlanName = '${appName}-${environment}-plan'
var functionAppName = '${appName}-${environment}-func'

resource hostingPlan 'Microsoft.Web/serverfarms@2023-01-01' = {
  name: hostingPlanName
  location: location
  kind: 'linux'
  tags: tags
  sku: {
    name: hostingPlanSku
    tier: hostingPlanTier
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
        { name: 'WEBSITE_CONTENTAZUREFILECONNECTIONSTRING', value: storageConnectionString }
        { name: 'WEBSITE_RUN_FROM_PACKAGE', value: '1' }
        { name: 'FUNCTIONS_EXTENSION_VERSION', value: '~4' }
        { name: 'FUNCTIONS_WORKER_RUNTIME', value: 'python' }
        { name: 'APPINSIGHTS_CONNECTIONSTRING', value: applicationInsightsConnectionString }
        { name: 'APPLICATIONINSIGHTS_CONNECTION_STRING', value: applicationInsightsConnectionString }
        { name: 'COSMOS_ENDPOINT', value: cosmosEndpoint }
        { name: 'COSMOS_KEY', value: cosmosKey }
        { name: 'COSMOS_DB_NAME', value: cosmosDbName }
        { name: 'COSMOS_CONTAINER_NAME', value: cosmosContainerName }
        { name: 'RAW_CONTAINER_NAME', value: 'raw' }
        { name: 'DOCUMENT_INTELLIGENCE_ENDPOINT', value: documentIntelligenceEndpoint }
        { name: 'DOCUMENT_INTELLIGENCE_API_KEY', value: documentIntelligenceApiKey }
        { name: 'AZURE_OPENAI_ENDPOINT', value: azureOpenAiEndpoint }
        { name: 'AZURE_OPENAI_API_KEY', value: azureOpenAiApiKey }
        { name: 'AZURE_OPENAI_DEPLOYMENT_NAME', value: azureOpenAiDeploymentName }
        { name: 'AZURE_OPENAI_API_VERSION', value: azureOpenAiApiVersion }
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
