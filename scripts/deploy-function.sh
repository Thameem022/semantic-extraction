#!/usr/bin/env bash
set -euo pipefail

RESOURCE_GROUP="${RESOURCE_GROUP:-semex-dev-rg}"
FUNCTION_APP="${FUNCTION_APP:-semex-dev-func}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
ZIP_FILE="${PROJECT_ROOT}/functionapp.zip"

rm -f "${ZIP_FILE}"

cd "${PROJECT_ROOT}"

# Add root-level files
zip -r "${ZIP_FILE}" host.json requirements.txt

# Add function folders and shared code without adding the parent "functions/" folder itself
cd functions
zip -r "${ZIP_FILE}" .
cd ..

# Deploy
az functionapp deployment source config-zip \
  --resource-group "${RESOURCE_GROUP}" \
  --name "${FUNCTION_APP}" \
  --src "${ZIP_FILE}" \
  --build-remote true

rm -f "${ZIP_FILE}"

echo "Deployment complete: ${FUNCTION_APP}"