# Shared Bicep core

Reusable Azure-first modules for the Intelligent Automation microhack labs. Defaults favor low cost and secure-by-default operation.

## Modules

- `modules/naming.bicep` creates deterministic names, a shared prefix, and a unique suffix from the resource group ID.
- `modules/logAnalytics.bicep` deploys Log Analytics with `PerGB2018`, 30-day retention, and a daily ingestion cap.
- `modules/appInsights.bicep` deploys workspace-based Application Insights for OpenTelemetry telemetry.
- `modules/managedIdentity.bicep` deploys a user-assigned managed identity for Entra-based access.
- `modules/keyVault.bicep` deploys RBAC-based Key Vault with soft delete, purge protection, and public access disabled unless a lab opts in.
- `modules/storageAccount.bicep` deploys StorageV2 with TLS 1.2, no shared keys, no public blob access, and public network access enabled by default so labs work without private endpoints. Production should disable public network access.
- `modules/roleAssignment.bicep` assigns common built-in roles using deterministic `guid()` names.
- `core/core.bicep` composes naming, Log Analytics, Application Insights, managed identity, and optional Key Vault as a platform foundation.

## Security choices

The modules prefer managed identity and Microsoft Entra authorization, disable shared keys where practical, enable Key Vault RBAC, enable soft delete and purge protection, enforce TLS 1.2 for storage, and send Key Vault audit diagnostics to Log Analytics from `core.bicep`.

## Cost controls

Defaults use free, consumption, or lowest-cost SKUs where possible: Log Analytics `PerGB2018` with a small daily quota, workspace-based Application Insights, Standard Key Vault, and Standard_LRS StorageV2. Labs can raise quotas or harden network access as needed.

## Consuming the core foundation

Deploy the foundation first, then pass its outputs to lab-specific modules for identity, telemetry, and Key Vault references.

```powershell
az deployment group create `
  --resource-group <resource-group-name> `
  --template-file infra\bicep\core\core.bicep `
  --parameters infra\bicep\core\core.bicepparam
```

## 📋 Evidence awareness

These IaC files double as ALM and governance evidence for Module B.3.2: they document repeatable deployment, cost controls, identity-first security, diagnostics, and resource tagging.
