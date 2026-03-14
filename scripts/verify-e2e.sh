#!/usr/bin/env bash
# Verify E2E pipeline after test-e2e.sh: check storage containers and Cosmos docs.
# Run 30–60 seconds after uploading to incoming.
set -euo pipefail

RESOURCE_GROUP="${RESOURCE_GROUP:-semex-dev-rg}"
STORAGE_ACCOUNT="${STORAGE_ACCOUNT:-}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [[ -z "${STORAGE_ACCOUNT}" ]]; then
  STORAGE_ACCOUNT=$(az storage account list -g "${RESOURCE_GROUP}" --query "[?starts_with(name, 'semex')].name | [0]" -o tsv)
  if [[ -z "${STORAGE_ACCOUNT}" || "${STORAGE_ACCOUNT}" == "None" ]]; then
    echo "No storage account found in ${RESOURCE_GROUP}."
    exit 1
  fi
fi

COSMOS_ACCOUNT=$(az cosmosdb list -g "${RESOURCE_GROUP}" --query "[?starts_with(name, 'semex')].name | [0]" -o tsv)
if [[ -z "${COSMOS_ACCOUNT}" || "${COSMOS_ACCOUNT}" == "None" ]]; then
  COSMOS_ACCOUNT=""
fi

echo "=== Storage: incoming (should be empty after ingest) ==="
az storage blob list --account-name "${STORAGE_ACCOUNT}" --container-name "incoming" -o table 2>/dev/null || true

echo ""
echo "=== Storage: raw (expect raw/<docId>/<filename>) ==="
az storage blob list --account-name "${STORAGE_ACCOUNT}" --container-name "raw" -o table 2>/dev/null || true

echo ""
echo "=== Storage: ocr-raw (expect ocr-raw/<docId>/document_intelligence.json) ==="
az storage blob list --account-name "${STORAGE_ACCOUNT}" --container-name "ocr-raw" -o table 2>/dev/null || true

echo ""
echo "=== Storage: ocr-layout (expect ocr-layout/<docId>/layout.json) ==="
az storage blob list --account-name "${STORAGE_ACCOUNT}" --container-name "ocr-layout" -o table 2>/dev/null || true

if [[ -n "${COSMOS_ACCOUNT}" ]]; then
  echo ""
  echo "=== Cosmos DB: latest 5 documents (semex / documents) ==="
  az cosmosdb sql container query \
    -g "${RESOURCE_GROUP}" \
    --account-name "${COSMOS_ACCOUNT}" \
    --database-name "semex" \
    --name "documents" \
    -q "SELECT c.docId, c.filename, c.status, c.uploadedAtUtc FROM c ORDER BY c.uploadedAtUtc DESC OFFSET 0 LIMIT 5" \
    -o table 2>/dev/null || echo "Cosmos query failed (check RBAC or account name)."
else
  echo ""
  echo "=== Cosmos: account not found in ${RESOURCE_GROUP}; skip Cosmos check or set COSMOS_ACCOUNT."
fi

echo ""
echo "=== Function log stream (Ctrl+C to stop) ==="
echo "  az webapp log tail -g ${RESOURCE_GROUP} -n semex-dev-func"
echo ""
