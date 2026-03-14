#!/usr/bin/env bash
# Delete the Function App, redeploy infra (recreates the app), then deploy function code.
# Requires: az logged in (uses current subscription if SUBSCRIPTION_ID not set).
set -euo pipefail

RESOURCE_GROUP="${RESOURCE_GROUP:-semex-dev-rg}"
FUNCTION_APP="${FUNCTION_APP:-semex-dev-func}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

echo "=== 1. Deleting Function App: ${FUNCTION_APP} ==="
az functionapp delete \
  --resource-group "${RESOURCE_GROUP}" \
  --name "${FUNCTION_APP}" \
  --yes 2>/dev/null || true

echo "=== 2. Redeploying infra (recreates Function App) ==="
if [[ -z "${SUBSCRIPTION_ID:-}" ]]; then
  SUBSCRIPTION_ID="$(az account show --query id -o tsv 2>/dev/null)" || true
fi
if [[ -z "${SUBSCRIPTION_ID:-}" ]]; then
  echo "SUBSCRIPTION_ID is not set and could not be read from 'az account show'. Set it and run again:"
  echo "  export SUBSCRIPTION_ID=your-subscription-id"
  echo "  ./scripts/rebuild-function.sh"
  exit 1
fi
export SUBSCRIPTION_ID
cd "${PROJECT_ROOT}/infra/scripts"
./deploy-dev.sh
cd "${PROJECT_ROOT}"

echo "=== 3. Deploying function code ==="
"${SCRIPT_DIR}/deploy-function.sh"

echo "=== Rebuild complete: ${FUNCTION_APP} ==="
