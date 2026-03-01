#!/usr/bin/env bash
# Deploy function code to Azure Function App via zip + remote build.
set -euo pipefail

RESOURCE_GROUP="${RESOURCE_GROUP:-semex-dev-rg}"
FUNCTION_APP="${FUNCTION_APP:-semex-dev-func}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

cd "${PROJECT_ROOT}"
zip -r functionapp.zip host.json requirements.txt
cd functions && zip -r ../functionapp.zip . && cd ..
az functionapp deployment source config-zip \
  -g "${RESOURCE_GROUP}" -n "${FUNCTION_APP}" \
  --src functionapp.zip --build-remote
rm functionapp.zip
echo "Deployment complete. Function App: ${FUNCTION_APP}"
