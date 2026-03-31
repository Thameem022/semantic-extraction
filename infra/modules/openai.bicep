// Azure OpenAI account + model deployment for cognitive / LLM extraction (fn_build_candidates).

@description('Application base name. Used for resource naming.')
param appName string

@description('Deployment environment (e.g. dev, prod).')
param environment string

@description('Azure region for Azure OpenAI (e.g. uaenorth). Must support the chosen model/version for your subscription.')
param location string

@description('Common resource tags.')
param tags object = {}

@description('OpenAI model id as shown in Azure AI Studio (e.g. gpt-4.1-nano).')
param modelName string = 'gpt-4.1-nano'

@description('Model version string (e.g. 2025-04-14 for gpt-4.1-nano).')
param modelVersion string = '2025-04-14'

@description('Deployment name on the account; must match AZURE_OPENAI_DEPLOYMENT_NAME (alphanumeric and hyphens).')
param deploymentName string = 'gpt-4-1-nano'

@description('Deployment capacity (units depend on sku.name; for GlobalStandard see Azure quota docs).')
param deploymentCapacity int = 10

var prefix = toLower('${replace(appName, '-', '')}${replace(environment, '-', '')}oai')
var accountName = '${prefix}${uniqueString(resourceGroup().id)}'

resource openAiAccount 'Microsoft.CognitiveServices/accounts@2023-05-01' = {
  name: accountName
  location: location
  kind: 'OpenAI'
  tags: tags
  sku: {
    name: 'S0'
  }
  properties: {
    customSubDomainName: accountName
    publicNetworkAccess: 'Enabled'
  }
}

// GPT-4.1 family: regional "Standard" pay-as-you-go is not valid; use Global Standard (see Foundry deployment types).
resource modelDeployment 'Microsoft.CognitiveServices/accounts/deployments@2024-06-01-preview' = {
  parent: openAiAccount
  name: deploymentName
  sku: {
    name: 'GlobalStandard'
    capacity: deploymentCapacity
  }
  properties: {
    model: {
      format: 'OpenAI'
      name: modelName
      version: modelVersion
    }
  }
}

var endpoint = openAiAccount.properties.endpoint
var primaryKey = openAiAccount.listKeys().key1

@description('Azure OpenAI account name.')
output openAiAccountName string = openAiAccount.name

@description('HTTPS endpoint for the Azure OpenAI resource.')
output openAiEndpoint string = endpoint

@description('Primary key for the Azure OpenAI resource.')
@secure()
output openAiPrimaryKey string = primaryKey

@description('Model deployment name (use as AZURE_OPENAI_DEPLOYMENT_NAME).')
output openAiDeploymentName string = deploymentName
