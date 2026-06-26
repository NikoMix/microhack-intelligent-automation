# Migration plan template

Use these sections **verbatim and in order** so every plan is comparable and reviewable. This is
the same structure the `draft_migration_plan` MCP tool emits.

```markdown
## Overview
- Workload: <what it does, who uses it, business criticality>
- Source: <Power Automate / Power Apps / Dataverse / connectors / AI Builder>
- Target cloud & config: <Azure; INFERENCE_PROVIDER for any AI step>
- Goals & non-goals

## Target architecture
- Source component → Azure landing service mapping (table)
- Identity: Entra ID / managed identity; secrets in Key Vault
- Networking & data flow (diagram or bullet description)
- Default to free/consumption tiers; note paid-tier upgrade paths

## Migration steps
1. Prepare (subscriptions, resource groups, identities)
2. Provision target services (prefer IaC: Bicep/Terraform)
3. Port logic (flows → Logic Apps/Functions; apps → App Service/SWA)
4. Migrate data (Dataverse → Azure SQL / Cosmos DB) with validation
5. Re-wire integrations (connectors → API Management)
6. Cut over and decommission the source

## Risks & mitigations
- <risk> → <mitigation> (one row per material risk: data loss, downtime,
  connector parity, throttling, cost overrun, security regression)

## Validation
- Functional parity tests, data reconciliation, load/perf checks
- Security review (identity, network, secrets) and cost check vs. estimate

## Rollback
- Trigger conditions, rollback steps, data restore approach, owner
```

## Guardrails checklist

- [ ] All six sections present and in order
- [ ] Every source component mapped to a named Azure service
- [ ] AI steps run on the shared modular-inference layer (no hard-coded provider)
- [ ] Entra ID / managed identity preferred; no secrets in the plan
- [ ] Free/consumption tier by default; paid upgrade path noted
- [ ] Cost & sizing flagged as estimates with a pointer to authoritative tools
