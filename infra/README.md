## Semantic Extraction Infra

This directory contains the modular Bicep infrastructure for the **semantic-extraction** project.

It deploys:
- A Storage Account with blob versioning, soft delete and containers.
- A workspace-based Monitoring stack (Log Analytics + Application Insights).
- A Linux Consumption plan and a Python 3.12 Azure Function App (v4) with managed identity.
- An RBAC role assignment granting the Function App managed identity **Storage Blob Data Contributor** on the storage account.

### Prerequisites

- Azure CLI (`az`) installed and logged in:

```bash
az login
az account list -o table
```

- Permissions to:
  - Create resource groups.
  - Deploy resource group-level templates.
  - Assign RBAC roles.

### Files

- `main.bicep`  
  Orchestrates all modules (`storage`, `monitoring`, `functionapp`, `rbac`) in a single resource-group deployment.

- `parameters.dev.json` / `parameters.prod.json`  
  Parameter files for dev and prod. They define:
  - `appName` (default `semex`)
  - `environment` (`dev` or `prod`)
  - `location` (e.g. `eastus`)
  - `retentionDays`
  - `tags` (arbitrary key/value pairs)

- `modules/storage.bicep`  
  Storage account + blob service configuration and containers: `incoming`, `raw`, `duplicates`, `rejected`.

- `modules/monitoring.bicep`  
  Log Analytics workspace + workspace-based Application Insights.

- `modules/functionapp.bicep`  
  Linux Consumption plan + Python 3.12 Function App (v4), system-assigned managed identity and app settings.

- `modules/rbac.bicep`  
  RBAC role assignment (`Storage Blob Data Contributor`) scoped to the storage account for the Function App managed identity, using a deterministic GUID.

- `scripts/deploy-dev.sh` / `scripts/deploy-prod.sh`  
  Helper scripts that:
  - Ensure the resource group exists.
  - Optionally run `az deployment group what-if` (skip with `SKIP_WHATIF=1`).
  - Run `az deployment group create`.

### Resource Naming

Resources follow the convention: `{appName}-{environment}-{suffix}`. Examples:

- Storage account: `semex-dev-sa`
- Function app: `semex-dev-func`
- Log Analytics workspace: `semex-dev-law`
- Application Insights: `semex-dev-ai`

### Deploying to Dev

From the repo root:

```bash
cd infra/scripts

export SUBSCRIPTION_ID="<your-subscription-id>"
# Optional: override defaults
export RESOURCE_GROUP_NAME="semex-dev-rg"
export LOCATION="eastus"

./deploy-dev.sh
```

The script will:
- Create the dev resource group if it does not exist.
- Run a what-if against `infra/main.bicep` with `parameters.dev.json` (unless `SKIP_WHATIF=1`).
- Apply the deployment.

To skip what-if (useful if you hit connection resets or throttling):

```bash
SKIP_WHATIF=1 ./deploy-dev.sh
```

### Deploying to Prod

From the repo root:

```bash
cd infra/scripts

export SUBSCRIPTION_ID="<your-subscription-id>"
# Optional: override defaults
export RESOURCE_GROUP_NAME="semex-prod-rg"
export LOCATION="eastus"

./deploy-prod.sh
```

The script will:
- Create the prod resource group if it does not exist.
- Run a what-if against `infra/main.bicep` with `parameters.prod.json`.
- Apply the deployment.

### Removing resources

To remove all deployed resources for an environment, delete the resource group. This permanently deletes the storage account, function app, monitoring resources, and any data in them.

**Dev:**

```bash
az account set --subscription "<your-subscription-id>"
az group delete --name semex-dev-rg --no-wait
```

**Prod:**

```bash
az account set --subscription "<your-subscription-id>"
az group delete --name semex-prod-rg --no-wait
```

- `--no-wait` returns immediately while Azure deletes the group in the background. Omit it to block until deletion completes.
- Azure may prompt for confirmation; use `--yes` (or `-y`) to skip the prompt in scripts or non-interactive use.

### Troubleshooting: Connection reset (10054)

If `az deployment group what-if` or `az deployment group create` fails with `ConnectionResetError(10054)` or "connection was forcibly closed", common causes are:

- **Long-running HTTPS to ARM** – what-if and create are heavy; transient blips or throttling (especially on free/low-quota subscriptions) can reset the connection.
- **VPN / corporate proxy / antivirus** – can close long-lived TLS connections.

**Quick fix:** Skip what-if and deploy only:

```bash
SKIP_WHATIF=1 ./deploy-dev.sh
```

Then retry. If the failure happens during `create`, retry the same command; often the second attempt succeeds.

### Customizing Parameters

Edit the parameter files in `infra/`:

- `parameters.dev.json`
- `parameters.prod.json`

You can change:
- `location` to another Azure region.
- `retentionDays` to adjust blob soft delete and log retention.
- `tags` to align with your tagging policy.

### Inspecting Deployment Outputs

To see outputs (e.g. storage account name, function app name, workspace name), run:

```bash
az deployment group show \
  --resource-group "<rg-name>" \
  --name "<deployment-name>" \
  --query "properties.outputs"
```

For example, after a dev deployment:

```bash
az deployment group show \
  --resource-group "semex-dev-rg" \
  --name "semex-dev-deployment" \
  --query "properties.outputs"
```

