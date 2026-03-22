#!/usr/bin/env bash
# Batch E2E test: upload multiple files to incoming; each triggers fn_ingest_blob then fn_run_ocr.
# Usage:
#   ./scripts/test-e2e-batch.sh /path/to/doc1.pdf /path/to/doc2.pdf ...
#   ./scripts/test-e2e-batch.sh /path/to/docs/*.pdf
# Requires: az logged in, RESOURCE_GROUP (same as test-e2e.sh).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
E2E_SCRIPT="${SCRIPT_DIR}/test-e2e.sh"

if [[ ! -x "${E2E_SCRIPT}" ]]; then
  echo "E2E script not found or not executable: ${E2E_SCRIPT}"
  exit 1
fi

if [[ $# -eq 0 ]]; then
  echo "Usage: $0 <file1> [file2 ...]"
  echo "Example: $0 /path/to/doc1.pdf /path/to/doc2.pdf"
  echo "Example: $0 ./test-docs/*.pdf"
  exit 1
fi

count=0
for f in "$@"; do
  if [[ ! -f "$f" ]]; then
    echo "Skipping (not a file): $f"
    continue
  fi
  count=$((count + 1))
  echo "=== [$count] Processing: $f ==="
  "${E2E_SCRIPT}" "$f"
  echo ""
done

echo "=== Batch complete: $count file(s) uploaded to incoming ==="
echo "Wait 30–60 seconds per document, then verify Cosmos and storage (see test-e2e.sh output)."
