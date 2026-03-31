# Semantic Extraction

Pipeline for ingesting policy documents into Cosmos DB and raw blob storage.

## Architecture (achieved so far)

End-to-end flow that is deployed and working:

1. **Blob upload** → User (or system) uploads a file to the **incoming** container (e.g. `auto/sample.pdf`).
2. **Blob trigger** → Azure Function **fn_ingest_blob** fires on `incoming/{name}`.
3. **Function logic** → Reads blob, computes SHA-256, gets properties/metadata, derives `policyType` (metadata or path prefix) and `original_filename`, then:
   - **Cosmos DB** – Upserts a document in **semex** / **documents** with `id`, `docId`, `filename`, `uploadedAtUtc`, `policyType`, `sha256`, `status: "RECEIVED"`, and blob metadata (duplicate SHA-256 is handled without failing the run).
   - **Raw storage** – Server-side copy to **raw** at `raw/{docId}/{original_filename}`.
   - **Cleanup** – Deletes the original blob from **incoming**.

**Components:**

| Component | Role |
|-----------|------|
| **Storage account** | Containers: `incoming`, `raw`, `duplicates`, `rejected`. `AzureWebJobsStorage` + Function App uses it for runtime and blob access. |
| **Cosmos DB (SQL)** | Account + database **semex** + container **documents** (partition key `/policyType`, unique key `/sha256`). Stores one document per ingested file. |
| **Function App** | Linux, Python 3.12, v4. Single function **fn_ingest_blob** (blob trigger). Uses **DefaultAzureCredential** for Cosmos; connection string for Storage. |
| **RBAC** | Function App managed identity has **Cosmos DB Built-in Data Contributor** (data plane, `sqlRoleAssignments`) and **Storage Blob Data Contributor** on the storage account. |

**Deploy layout that works:** Zip must have `host.json` and `requirements.txt` at the **root**, and function folders (e.g. `fn_ingest_blob/`) also at the root (i.e. zip the *contents* of `functions/`, not the `functions/` folder itself). `host.json` must use an extension bundle that includes Blob Storage bindings (e.g. `Microsoft.Azure.Functions.ExtensionBundle` version `[4.*, 5.0.0)`).

**Verified:** Upload to `incoming` (e.g. `auto/sample3.pdf`) → document in Cosmos with `status: RECEIVED` and blob at `raw/{docId}/sample3.pdf` (and source removed from `incoming`).

---

## Milestone 1 test

1. **Deploy infra**

   ```bash
   cd infra/scripts
   export SUBSCRIPTION_ID="<your-subscription-id>"
   ./deploy-dev.sh
   ```

2. **Deploy function code**

   From the repo root. Preferred: use a Python 3.12 virtual environment to avoid version mismatch.

   **Option A – Core Tools (remote build):**
   ```bash
   func azure functionapp publish semex-dev-func --python
   ```

   **Option B – Zip deploy (if Option A times out on SCM):**  
   Zip must have `host.json` and `requirements.txt` at root and each function folder (e.g. `fn_ingest_blob/`) at root too (not under `functions/`):
   ```bash
   zip -r functionapp.zip host.json requirements.txt
   cd functions && zip -r ../functionapp.zip . && cd ..
   az functionapp deployment source config-zip \
     -g semex-dev-rg -n semex-dev-func \
     --src functionapp.zip --build-remote
   rm functionapp.zip
   ```

   Or run the helper script:
   ```bash
   ./scripts/deploy-function.sh
   ```

   Use the actual Function App name from your deployment outputs (e.g. from `az deployment group show ... --query "properties.outputs.functionAppName.value"`).

   **If you see SCM timeouts or JSON parse errors:** `WEBSITE_CONTENTOVERVNET` was removed from the Function App (no VNet in use). Redeploy infra (`./deploy-dev.sh`), wait 2–3 minutes, then retry.

3. **Upload a PDF to incoming**

   Example using Azure CLI:

   ```bash
   STORAGE_ACCOUNT="<storage-account-name-from-outputs>"
   az storage blob upload \
     --account-name "$STORAGE_ACCOUNT" \
     --container-name incoming \
     --name "test-policy/sample.pdf" \
     --file ./sample.pdf
   ```

   Or with SAS or connection string:

   ```bash
   az storage blob upload \
     --connection-string "<connection-string>" \
     --container-name incoming \
     --name "test-policy/sample.pdf" \
     --file ./sample.pdf
   ```

4. **Verify**

   - Cosmos doc created with `status: RECEIVED` and `id`/`docId` populated.
   - Raw blob exists at `raw/{docId}/{filename}`.
   - Function logs show step markers: `RECEIVED`, `COSMOS_UPSERT_OK`, `COPY_STARTED`, `COPY_SUCCEEDED`, `INCOMING_DELETED`.

**Quick E2E test (ingest + OCR):**

   From repo root (uses storage account in the same resource group):

   ```bash
   ./scripts/test-e2e.sh
   ```

   Or with a specific file (e.g. a PDF for full OCR):

   ```bash
   ./scripts/test-e2e.sh /path/to/sample.pdf
   ```

   Then wait 30–60 seconds and check:
   - Cosmos: document moves from `RECEIVED` → `OCR_STARTED` → `OCR_COMPLETE`.
   - Storage: `raw/<docId>/<filename>`, `ocr-raw/<docId>/document_intelligence.json`, `ocr-layout/<docId>/layout.json`.
   - Log stream: `az webapp log tail -g semex-dev-rg -n semex-dev-func`.

---

## Running unit tests

Use the project venv and run tests from repo root:

```bash
# One-time: create venv and install deps
python3 -m venv .venv
.venv/bin/pip install -r requirements-dev.txt

# Run tests (uses .venv automatically)
./scripts/run-tests.sh
```

Or with coverage:

```bash
.venv/bin/python -m pytest tests/ -v --cov=shared --cov-report=term-missing
```

Tests live under `tests/unit/` and cover `shared.blob_paths`, `shared.statuses`, `shared.layout_normalizer`, and `fn_run_ocr._parse_raw_blob_name`.

---

## Local Development (Frontend + API)

### 1. Configure backend settings

1. Update `local.settings.json` at the repo root with your Cosmos DB values:
   - `COSMOS_ENDPOINT`
   - `COSMOS_KEY`
   - `COSMOS_DB_NAME`
   - `COSMOS_CONTAINER_NAME`
2. Ensure `AzureWebJobsStorage` is set to your Azure Storage connection string.

### 2. Start the Azure Functions host

From the repo root:

```bash
func start --python
```

The HTTP endpoints will be available at `http://localhost:7071/api/`:
- `POST /api/fn_http_upload`
- `GET  /api/fn_http_status?docId=<uuid>`

### 3. Start the web UI

From the repo root:

```bash
cd frontend
cat > .env.local <<'EOF'
NEXT_PUBLIC_FUNCTION_BASE_URL=http://localhost:7071
EOF
npm install
npm run dev
```

Then open `http://localhost:3000`.

The frontend uses `NEXT_PUBLIC_FUNCTION_BASE_URL` (defaults to `http://localhost:7071`).

### 4. Upload + view extraction results

Use the drag-and-drop zone to upload a PDF. The UI will:
1. Call `fn_http_upload` to create a `docId`
2. Poll `fn_http_status` every ~2.5 seconds until `CANDIDATES_GENERATED`
3. Render the returned extracted field candidates
