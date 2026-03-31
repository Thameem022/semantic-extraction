#!/usr/bin/env bash
set -euo pipefail

# Start Azure Functions locally from a staged app root where function folders
# are top-level (same layout used for deployment package).
#
# Usage:
#   ./scripts/run-func-local.sh
#   ./scripts/run-func-local.sh --port 7071

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STAGE_DIR="${ROOT_DIR}/.func-local-root"
PORT="7071"

if [[ "${1:-}" == "--port" && -n "${2:-}" ]]; then
  PORT="$2"
fi

rm -rf "${STAGE_DIR}"
mkdir -p "${STAGE_DIR}"

# Host/runtime files must be at app root.
cp "${ROOT_DIR}/host.json" "${STAGE_DIR}/host.json"
cp "${ROOT_DIR}/requirements.txt" "${STAGE_DIR}/requirements.txt"

# Keep local settings for storage/cosmos keys.
if [[ -f "${ROOT_DIR}/local.settings.json" ]]; then
  cp "${ROOT_DIR}/local.settings.json" "${STAGE_DIR}/local.settings.json"
fi

# Function directories must be top-level for Core Tools discovery.
for fn_dir in "${ROOT_DIR}"/functions/*; do
  if [[ -d "${fn_dir}" ]]; then
    fn_name="$(basename "${fn_dir}")"
    cp -R "${fn_dir}" "${STAGE_DIR}/${fn_name}"
  fi
done

echo "Starting Functions from staged app root: ${STAGE_DIR}"
echo "Port: ${PORT}"
cd "${STAGE_DIR}"
exec func start --python --port "${PORT}"

