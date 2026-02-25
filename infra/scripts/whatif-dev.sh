#!/usr/bin/env bash
set -euo pipefail

RESOURCE_GROUP="rg-semext-dev"

echo "Running what-if for dev deployment in resource group ${RESOURCE_GROUP}..."
az deployment group what-if \
  --resource-group "${RESOURCE_GROUP}" \
  --template-file "$(dirname "$0")/../main.bicep" \
  --parameters "$(dirname "$0")/../parameters.dev.json"

