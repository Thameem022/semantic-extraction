#!/usr/bin/env bash
set -euo pipefail

SUBSCRIPTION_ID="${SUBSCRIPTION_ID:-}"
RESOURCE_GROUP_NAME="${RESOURCE_GROUP_NAME:-semex-dev-rg}"
LOCATION="${LOCATION:-eastus}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PARAM_FILE="${SCRIPT_DIR}/../parameters.dev.json"
DEPLOYMENT_NAME="${DEPLOYMENT_NAME:-semex-dev-deployment}"

if [[ -z "${SUBSCRIPTION_ID}" ]]; then
  echo "SUBSCRIPTION_ID environment variable must be set."
  exit 1
fi

echo "Using subscription: ${SUBSCRIPTION_ID}"
az account set --subscription "${SUBSCRIPTION_ID}"

if ! az group show --name "${RESOURCE_GROUP_NAME}" >/dev/null 2>&1; then
  echo "Creating resource group ${RESOURCE_GROUP_NAME} in ${LOCATION}..."
  az group create \
    --name "${RESOURCE_GROUP_NAME}" \
    --location "${LOCATION}" \
    --tags environment=dev project=semantic-extraction
else
  echo "Resource group ${RESOURCE_GROUP_NAME} already exists."
fi

echo "Running what-if for deployment ${DEPLOYMENT_NAME}..."
az deployment group what-if \
  --resource-group "${RESOURCE_GROUP_NAME}" \
  --name "${DEPLOYMENT_NAME}" \
  --template-file "${SCRIPT_DIR}/../main.bicep" \
  --parameters "@${PARAM_FILE}"

echo "Running create/update deployment ${DEPLOYMENT_NAME}..."
az deployment group create \
  --resource-group "${RESOURCE_GROUP_NAME}" \
  --name "${DEPLOYMENT_NAME}" \
  --template-file "${SCRIPT_DIR}/../main.bicep" \
  --parameters "@${PARAM_FILE}"
