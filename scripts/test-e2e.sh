#!/usr/bin/env bash
# End-to-end test: upload a file to incoming, then verify Cosmos + raw + ocr-raw/ocr-layout.
# Requires: az logged in, RESOURCE_GROUP and optionally a test file path.
set -euo pipefail

RESOURCE_GROUP="${RESOURCE_GROUP:-semex-dev-rg}"
STORAGE_ACCOUNT="${STORAGE_ACCOUNT:-}"
TEST_FILE="${1:-}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

if [[ -z "${STORAGE_ACCOUNT}" ]]; then
  echo "Resolving storage account in resource group ${RESOURCE_GROUP}..."
  STORAGE_ACCOUNT=$(az storage account list -g "${RESOURCE_GROUP}" --query "[?starts_with(name, 'semex')].name | [0]" -o tsv)
  if [[ -z "${STORAGE_ACCOUNT}" || "${STORAGE_ACCOUNT}" == "None" ]]; then
    echo "No storage account found in ${RESOURCE_GROUP}. Deploy infra first."
    exit 1
  fi
  echo "Using storage account: ${STORAGE_ACCOUNT}"
fi

# Create a small test file if none given (removed after upload)
CREATED_TEMP_FILE=""
if [[ -z "${TEST_FILE}" || ! -f "${TEST_FILE}" ]]; then
  TEST_FILE="${PROJECT_ROOT}/.test-sample.txt"
  echo "No valid test file provided. Creating ${TEST_FILE}"
  echo "Sample document for semantic-extraction E2E test at $(date -u +%Y-%m-%dT%H:%M:%SZ)" > "${TEST_FILE}"
  CREATED_TEMP_FILE=1
fi

echo "=== Uploading to container 'incoming': $(basename "${TEST_FILE}") ==="
az storage blob upload \
  --account-name "${STORAGE_ACCOUNT}" \
  --container-name "incoming" \
  --name "test/$(basename "${TEST_FILE}")" \
  --file "${TEST_FILE}" \
  --overwrite

echo ""
echo "=== Triggered: fn_ingest_blob (incoming -> Cosmos + raw) then fn_run_ocr (raw -> Document Intelligence) ==="
echo "Wait 30–60 seconds, then verify:"
echo ""
echo "  1. Cosmos DB (semex / documents): new document with status RECEIVED -> OCR_STARTED -> OCR_COMPLETE"
echo "  2. Storage:"
echo "     - incoming: blob removed (moved to raw)"
echo "     - raw/<docId>/$(basename "${TEST_FILE}"): copy of the file"
echo "     - ocr-raw/<docId>/document_intelligence.json: raw Document Intelligence response"
echo "     - ocr-layout/<docId>/layout.json: normalized layout"
echo ""
echo "  Cosmos (az CLI):"
echo "    az cosmosdb sql container query -g ${RESOURCE_GROUP} --account-name <cosmos-name> --database-name semex --name documents -q \"SELECT * FROM c ORDER BY c.uploadedAtUtc DESC OFFSET 0 LIMIT 5\""
echo ""
echo "  List blobs in raw:"
echo "    az storage blob list -c raw --account-name ${STORAGE_ACCOUNT} -o table"
echo ""
echo "  List blobs in ocr-raw:"
echo "    az storage blob list -c ocr-raw --account-name ${STORAGE_ACCOUNT} -o table"
echo ""
echo "  Function logs (Application Insights or Log stream):"
echo "    az webapp log tail -g ${RESOURCE_GROUP} -n semex-dev-func"
echo ""

# Remove temp file if we created it
if [[ -n "${CREATED_TEMP_FILE:-}" && -f "${TEST_FILE:-}" ]]; then
  rm -f "${TEST_FILE}"
  echo "Removed temporary test file: ${TEST_FILE}"
fi
