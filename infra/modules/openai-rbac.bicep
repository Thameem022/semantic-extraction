// Grants the Function App managed identity "Cognitive Services OpenAI User" on the OpenAI account
// (for keyless / future use; app settings may still use API key).

@description('Name of the existing Azure OpenAI (Cognitive Services) account.')
param openAiAccountName string

@description('Principal ID of the Function App system-assigned identity.')
param principalId string

// Cognitive Services OpenAI User — see built-in roles (AI + machine learning).
var cognitiveServicesOpenAIUserRoleId = '5e0bd9bd-7b93-4f28-af87-19fc36ad61bd'

resource openAiAccount 'Microsoft.CognitiveServices/accounts@2023-05-01' existing = {
  name: openAiAccountName
}

resource openAiUserAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(openAiAccount.id, principalId, cognitiveServicesOpenAIUserRoleId)
  scope: openAiAccount
  properties: {
    roleDefinitionId: subscriptionResourceId(
      'Microsoft.Authorization/roleDefinitions',
      cognitiveServicesOpenAIUserRoleId
    )
    principalId: principalId
    principalType: 'ServicePrincipal'
  }
}
