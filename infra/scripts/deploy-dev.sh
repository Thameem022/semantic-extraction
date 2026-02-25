#!/usr/bin/env bash
set -euo pipefail

RESOURCE_GROUP="rg-semext-dev"
LOCATION="eastus"
DEPLOYMENT_NAME="semext-dev-$(date +%Y%m%d%H%M%S)"

echo "Ensuring resource group ${RESOURCE_GROUP} exists in ${LOCATION}..."
az group create \
  --name "${RESOURCE_GROUP}" \
  --location "${LOCATION}" \
  >/dev/null

echo "Deploying Bicep template to resource group ${RESOURCE_GROUP}..."
az deployment group create \
  --resource-group "${RESOURCE_GROUP}" \
  --name "${DEPLOYMENT_NAME}" \
  --template-file "$(dirname "$0")/../main.bicep" \
  --parameters "$(dirname "$0")/../parameters.dev.json"

echo "Deployment complete."

